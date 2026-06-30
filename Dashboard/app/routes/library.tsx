import { useState, useEffect, useCallback, useRef } from 'react';
import { UploadCloud, Search, AlertCircle } from 'lucide-react';
import { ErrorMessage } from '../components/ErrorMessage';
import {
  getFiles,
  uploadFile,
  deleteFile,
  getFileDownloadUrl,
  retryFileProcessing,
} from '../services/libraryService';
import type { LibraryFile } from '../types/library';
import { getApiErrorMessage } from '../utils/apiError';
import { confirmDeletion } from '../utils/confirmDeletion';
import { EmptyState } from '../components/EmptyState';
import { useTransientMessages } from '../hooks/useTransientMessages';
import {
  LibraryUploadZone,
  type UploadProgress,
} from '../components/LibraryUploadZone';
import { LibraryFileCard } from '../components/LibraryFileCard';
import { LibrarySkeleton } from '../components/PageSkeletons';

const ALLOWED_TYPES = ['pdf', 'pptx'];
const MAX_SIZE_MB = 50;
let cachedLibraryFiles: LibraryFile[] | null = null;
let cachedUploadingFiles: UploadProgress[] = [];

const libraryFileListeners = new Set<(files: LibraryFile[]) => void>();
const uploadProgressListeners = new Set<(uploads: UploadProgress[]) => void>();
const pendingUploadNames = new Set<string>();

function setCachedLibraryFiles(files: LibraryFile[]) {
  cachedLibraryFiles = files;
  libraryFileListeners.forEach((listener) => listener(files));
}

function updateCachedUploadingFiles(
  updater: (current: UploadProgress[]) => UploadProgress[],
) {
  cachedUploadingFiles = updater(cachedUploadingFiles);
  const snapshot = [...cachedUploadingFiles];
  uploadProgressListeners.forEach((listener) => listener(snapshot));
}

export default function Library() {
  const [files, setFiles] = useState<LibraryFile[]>(
    () => cachedLibraryFiles ?? [],
  );
  const [loading, setLoading] = useState(
    () => cachedLibraryFiles === null && cachedUploadingFiles.length === 0,
  );
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadProgress[]>(
    () => cachedUploadingFiles,
  );
  const [deletingFileIds, setDeletingFileIds] = useState<Set<string>>(
    () => new Set(),
  );
  const {
    messages: errors,
    replaceMessages: setErrors,
    appendMessage: appendError,
  } = useTransientMessages();

  // Always holds the latest files array — fixes stale closure in useCallback handlers
  const filesRef = useRef<LibraryFile[]>([]);
  const dragDepthRef = useRef(0);
  const mountedRef = useRef(false);

  // Keep ref in sync with state
  const updateFiles = useCallback((newFiles: LibraryFile[]) => {
    filesRef.current = newFiles;
    setCachedLibraryFiles(newFiles);
  }, []);

  const fetchFiles = useCallback(async () => {
    const hasVisibleSnapshot =
      cachedLibraryFiles !== null || cachedUploadingFiles.length > 0;
    try {
      if (!hasVisibleSnapshot) setLoading(true);
      setError(null);
      const data = await getFiles();
      if (!mountedRef.current) return;
      updateFiles(data);
    } catch (err) {
      if (!mountedRef.current) return;
      const message = getApiErrorMessage(err, 'Failed to load library files.');
      if (cachedLibraryFiles !== null || cachedUploadingFiles.length > 0) {
        appendError(`${message} Showing the latest cached files.`);
      } else {
        setError(message);
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [appendError, updateFiles]);

  useEffect(() => {
    mountedRef.current = true;
    const syncFiles = (nextFiles: LibraryFile[]) => {
      filesRef.current = nextFiles;
      setFiles(nextFiles);
    };
    const syncUploads = (nextUploads: UploadProgress[]) => {
      setUploadingFiles(nextUploads);
    };

    libraryFileListeners.add(syncFiles);
    uploadProgressListeners.add(syncUploads);

    if (cachedLibraryFiles) syncFiles(cachedLibraryFiles);
    syncUploads(cachedUploadingFiles);

    void fetchFiles();
    return () => {
      mountedRef.current = false;
      libraryFileListeners.delete(syncFiles);
      uploadProgressListeners.delete(syncUploads);
    };
  }, [fetchFiles]);

  useEffect(() => {
    const hasActiveProcessing = files.some((file) =>
      ['queued', 'processing'].includes(file.processingStatus),
    );
    if (!hasActiveProcessing) return;
    let active = true;
    let timer: number | undefined;
    const poll = async () => {
      try {
        const nextFiles = await getFiles();
        if (active) updateFiles(nextFiles);
      } catch {
        // A later poll can recover from a temporary network failure.
      } finally {
        if (active) timer = window.setTimeout(poll, 2500);
      }
    };
    timer = window.setTimeout(poll, 2500);
    return () => {
      active = false;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [files, updateFiles]);

  // ── Validation ────────────────────────────────
  const validateFile = (file: File): string | null => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !ALLOWED_TYPES.includes(ext)) {
      return `"${file.name}" — unsupported type. Allowed: PDF, PPTX`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `"${file.name}" — exceeds ${MAX_SIZE_MB}MB limit`;
    }
    return null;
  };

  // ── Upload with server-reported progress ──────
  const uploadSelectedFile = useCallback(
    async (file: File) => {
      const uploadId = crypto.randomUUID();
      updateCachedUploadingFiles((current) => [
        ...current,
        { id: uploadId, name: file.name, progress: 0 },
      ]);

      try {
        const saved = await uploadFile(file, (progress) => {
          updateCachedUploadingFiles((current) =>
            current.map((item) =>
              item.id === uploadId ? { ...item, progress } : item,
            ),
          );
        });
        const latestFiles = cachedLibraryFiles ?? filesRef.current;
        updateFiles([
          saved,
          ...latestFiles.filter((item) => item.id !== saved.id),
        ]);
      } catch (error) {
        if (mountedRef.current) {
          appendError(
            getApiErrorMessage(error, `Failed to upload "${file.name}".`),
          );
        }
      } finally {
        updateCachedUploadingFiles((current) =>
          current.filter((item) => item.id !== uploadId),
        );
        pendingUploadNames.delete(file.name.toLowerCase());
      }
    },
    [appendError, updateFiles],
  );

  // ── Process Files ─────────────────────────────
  const processFiles = useCallback(
    (fileList: FileList | File[]) => {
      const newErrors: string[] = [];
      const validFiles: File[] = [];
      const reservedNames = new Set([
        ...filesRef.current.map((file) => file.name.toLowerCase()),
        ...pendingUploadNames,
      ]);

      Array.from(fileList).forEach((file) => {
        const normalizedName = file.name.toLowerCase();
        if (reservedNames.has(normalizedName)) {
          newErrors.push(`"${file.name}" — already exists in your library`);
          return;
        }

        const error = validateFile(file);
        if (error) newErrors.push(error);
        else {
          reservedNames.add(normalizedName);
          pendingUploadNames.add(normalizedName);
          validFiles.push(file);
        }
      });

      if (newErrors.length > 0) {
        setErrors(newErrors);
      }

      validFiles.forEach((file) => void uploadSelectedFile(file));
    },
    [setErrors, uploadSelectedFile],
  );

  // ── Drag Handlers ─────────────────────────────
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepthRef.current += 1;
    setIsDragging(true);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = 'copy';
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
    if (dragDepthRef.current === 0) setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragDepthRef.current = 0;
      setIsDragging(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processFiles(e.dataTransfer.files);
      }
    },
    [processFiles],
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
      e.target.value = '';
    }
  };

  const handleDelete = async (file: LibraryFile) => {
    const confirmed = await confirmDeletion({
      text: `"${file.name}" will be permanently removed from your library.`,
      confirmButtonText: 'Delete file',
    });
    if (!confirmed) return;

    setDeletingFileIds((current) => new Set(current).add(file.id));
    try {
      await deleteFile(file.id);
      updateFiles(filesRef.current.filter((f) => f.id !== file.id));
    } catch (err) {
      setErrors([getApiErrorMessage(err, 'Failed to delete file.')]);
    } finally {
      setDeletingFileIds((current) => {
        const next = new Set(current);
        next.delete(file.id);
        return next;
      });
    }
  };

  const handleOpen = async (file: LibraryFile) => {
    const presentationWindow = window.open('about:blank', '_blank');
    try {
      const url = await getFileDownloadUrl(file.id);
      if (presentationWindow) {
        presentationWindow.opener = null;
        presentationWindow.location.replace(url);
      } else {
        window.location.assign(url);
      }
    } catch (err) {
      presentationWindow?.close();
      setErrors([getApiErrorMessage(err, 'Failed to open presentation.')]);
    }
  };

  const handleRetry = async (file: LibraryFile) => {
    try {
      const updated = await retryFileProcessing(file.id);
      updateFiles(
        filesRef.current.map((item) => (item.id === file.id ? updated : item)),
      );
    } catch (err) {
      setErrors([getApiErrorMessage(err, 'Failed to retry conversion.')]);
    }
  };

  const filtered = files.filter((f) =>
    f.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-black tracking-tight">Content Library</h1>
        <p className="text-[#d9d9d9] mt-1">
          Upload and manage materials for your VR training sessions.
        </p>
      </div>

      {loading && <LibrarySkeleton />}
      {error && <ErrorMessage message={error} onRetry={fetchFiles} />}

      {!loading && !error && (
        <>
          {/* Error Messages */}
          {errors.length > 0 && (
            <div
              role="alert"
              className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20"
            >
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-red-400 font-bold text-sm mb-1">
                    {errors.length} operation{errors.length > 1 ? 's' : ''}{' '}
                    failed:
                  </p>
                  {errors.map((err, i) => (
                    <p key={i} className="text-red-400/80 text-xs">
                      {err}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}

          <LibraryUploadZone
            isDragging={isDragging}
            uploads={uploadingFiles}
            maxSizeMb={MAX_SIZE_MB}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onFileInput={handleFileInput}
          />

          {/* Files Header & Search */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <h2 className="text-white text-xl font-black">
              Your Files
              <span className="text-[#aeb4a8] text-sm font-normal ml-2">
                ({filtered.length} {filtered.length === 1 ? 'file' : 'files'})
              </span>
            </h2>
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#aeb4a8]" />
              <input
                type="text"
                placeholder="Search files..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-[#121610] border border-[#46513c] rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder:text-[#aeb4a8] focus:outline-none focus:border-brand"
              />
            </div>
          </div>

          {/* Files Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map((file) => (
              <LibraryFileCard
                key={file.id}
                file={file}
                isDeleting={deletingFileIds.has(file.id)}
                onOpen={(item) => void handleOpen(item)}
                onRetry={(item) => void handleRetry(item)}
                onDelete={(item) => void handleDelete(item)}
              />
            ))}

            {filtered.length === 0 && uploadingFiles.length === 0 && (
              <div className="col-span-full">
                {search ? (
                  <EmptyState
                    icon={Search}
                    title="No matching files"
                    description={`No library files match "${search}". Try a different search term.`}
                  />
                ) : (
                  <EmptyState
                    icon={UploadCloud}
                    title="No files yet"
                    description="Upload your first PDF or PowerPoint presentation to use in your training sessions."
                  />
                )}
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}
