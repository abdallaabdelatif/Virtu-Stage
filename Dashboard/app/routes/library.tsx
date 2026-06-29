import { useState, useEffect, useCallback, useRef } from "react";
import { PageLayout } from "../components/PageLayout";
import { ProtectedRoute } from "../components/ProtectedRoute";
import {
  UploadCloud,
  FileType,
  Trash2,
  Search,
  AlertCircle,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErrorMessage } from "../components/ErrorMessage";
import {
  getFiles,
  uploadFile,
  deleteFile,
  getFileDownloadUrl,
  retryFileProcessing,
} from "../services/libraryService";
import type { LibraryFile } from "../types/library";
import { getApiErrorMessage } from "../utils/apiError";
import { confirmDeletion } from "../utils/confirmDeletion";
import { EmptyState } from "../components/EmptyState";

const ALLOWED_TYPES = ["pdf", "pptx"];
const MAX_SIZE_MB = 50;

interface UploadingFile {
  name: string;
  progress: number;
}

export default function Library() {
  const [files, setFiles] = useState<LibraryFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [deletingFileIds, setDeletingFileIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [errors, setErrors] = useState<string[]>([]);

  // Always holds the latest files array — fixes stale closure in useCallback handlers
  const filesRef = useRef<LibraryFile[]>([]);
  const dragDepthRef = useRef(0);

  // Keep ref in sync with state
  const updateFiles = (newFiles: LibraryFile[]) => {
    filesRef.current = newFiles;
    setFiles(newFiles);
  };

  const fetchFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFiles();
      updateFiles(data);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to load library files."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  useEffect(() => {
    const hasActiveProcessing = files.some((file) =>
      ["queued", "processing"].includes(file.processingStatus),
    );
    if (!hasActiveProcessing) return;
    const timer = window.setInterval(() => {
      void getFiles()
        .then(updateFiles)
        .catch(() => undefined);
    }, 2500);
    return () => window.clearInterval(timer);
  }, [files]);

  // ── Validation ────────────────────────────────
  const validateFile = (file: File): string | null => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !ALLOWED_TYPES.includes(ext)) {
      return `"${file.name}" — unsupported type. Allowed: PDF, PPTX`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `"${file.name}" — exceeds ${MAX_SIZE_MB}MB limit`;
    }
    return null;
  };

  // ── Upload with server-reported progress ──────
  const uploadSelectedFile = async (file: File) => {
    setUploadingFiles((current) => [
      ...current,
      { name: file.name, progress: 0 },
    ]);

    try {
      const saved = await uploadFile(file, (progress) => {
        setUploadingFiles((current) =>
          current.map((item) =>
            item.name === file.name ? { ...item, progress } : item,
          ),
        );
      });
      updateFiles([saved, ...filesRef.current]);
    } catch (error) {
      setErrors((current) => [
        ...current,
        getApiErrorMessage(error, `Failed to upload "${file.name}".`),
      ]);
    } finally {
      setUploadingFiles((current) =>
        current.filter((item) => item.name !== file.name),
      );
    }
  };

  // ── Process Files ─────────────────────────────
  const processFiles = useCallback((fileList: FileList | File[]) => {
    const newErrors: string[] = [];
    const validFiles: File[] = [];

    Array.from(fileList).forEach((file) => {
      // Duplicate check — uses ref so always reads latest files, never stale
      const alreadyExists = filesRef.current.some(
        (f) => f.name.toLowerCase() === file.name.toLowerCase(),
      );
      if (alreadyExists) {
        newErrors.push(`"${file.name}" — already exists in your library`);
        return;
      }

      const error = validateFile(file);
      if (error) newErrors.push(error);
      else validFiles.push(file);
    });

    if (newErrors.length > 0) {
      setErrors(newErrors);
      setTimeout(() => setErrors([]), 5000);
    }

    validFiles.forEach((file) => void uploadSelectedFile(file));
  }, []);

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
    e.dataTransfer.dropEffect = "copy";
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
      e.target.value = "";
    }
  };

  const handleDelete = async (file: LibraryFile) => {
    const confirmed = await confirmDeletion({
      text: `"${file.name}" will be permanently removed from your library.`,
      confirmButtonText: "Delete file",
    });
    if (!confirmed) return;

    setDeletingFileIds((current) => new Set(current).add(file.id));
    try {
      await deleteFile(file.id);
      updateFiles(filesRef.current.filter((f) => f.id !== file.id));
    } catch (err) {
      setErrors([getApiErrorMessage(err, "Failed to delete file.")]);
      setTimeout(() => setErrors([]), 5000);
    } finally {
      setDeletingFileIds((current) => {
        const next = new Set(current);
        next.delete(file.id);
        return next;
      });
    }
  };

  const handleOpen = async (file: LibraryFile) => {
    const presentationWindow = window.open("about:blank", "_blank");
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
      setErrors([getApiErrorMessage(err, "Failed to open presentation.")]);
      setTimeout(() => setErrors([]), 5000);
    }
  };

  const handleRetry = async (file: LibraryFile) => {
    try {
      const updated = await retryFileProcessing(file.id);
      updateFiles(
        filesRef.current.map((item) => (item.id === file.id ? updated : item)),
      );
    } catch (err) {
      setErrors([getApiErrorMessage(err, "Failed to retry conversion.")]);
      setTimeout(() => setErrors([]), 5000);
    }
  };

  const filtered = files.filter((f) =>
    f.name.toLowerCase().includes(search.toLowerCase()),
  );

  const isUploading = uploadingFiles.length > 0;

  return (
    <ProtectedRoute allowedRoles={["user"]}>
      <PageLayout>
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-black tracking-tight">
            Content Library
          </h1>
          <p className="text-[#9aa1bc] mt-1">
            Upload and manage materials for your VR training sessions.
          </p>
        </div>

        {loading && <LoadingSpinner text="Loading your files..." />}
        {error && <ErrorMessage message={error} onRetry={fetchFiles} />}

        {!loading && !error && (
          <>
            {/* Error Messages */}
            {errors.length > 0 && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-red-400 font-bold text-sm mb-1">
                      {errors.length} operation{errors.length > 1 ? "s" : ""}{" "}
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

            {/* Upload Area */}
            <div
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className={`relative w-full rounded-3xl border-2 border-dashed flex flex-col items-center justify-center transition-all duration-300 ease-out mb-8 ${
                isUploading ? "h-auto py-6 px-6" : "h-64"
              } ${
                isDragging
                  ? "border-[#5c7cff] bg-[#5c7cff]/5"
                  : "border-[#393f56] bg-[#12141c] hover:border-[#5c6484] hover:bg-[#1b1d28]"
              }`}
            >
              {isUploading ? (
                <div className="w-full max-w-md space-y-4">
                  <div className="flex items-center gap-3 mb-2">
                    <UploadCloud className="w-6 h-6 text-[#5c7cff] animate-bounce" />
                    <p className="text-white font-bold">
                      Uploading {uploadingFiles.length} file
                      {uploadingFiles.length > 1 ? "s" : ""}...
                    </p>
                  </div>
                  {uploadingFiles.map((f) => (
                    <div key={f.name}>
                      <div className="flex justify-between mb-1">
                        <p className="text-[#9aa1bc] text-xs truncate max-w-[80%]">
                          {f.name}
                        </p>
                        <p className="text-[#5c7cff] text-xs font-bold">
                          {f.progress}%
                        </p>
                      </div>
                      <div className="w-full h-1.5 bg-[#272b3a] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#5c7cff] transition-all duration-200 rounded-full"
                          style={{ width: `${f.progress}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  <div
                    className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors ${
                      isDragging
                        ? "bg-[#5c7cff]/20 text-[#5c7cff]"
                        : "bg-[#272b3a] text-[#9aa1bc]"
                    }`}
                  >
                    <UploadCloud className="w-8 h-8" />
                  </div>
                  <h3 className="text-white text-lg font-black tracking-tight mb-2">
                    Click or drag files to upload
                  </h3>
                  <p className="text-[#5c6484] text-sm mb-6 max-w-md text-center">
                    Supported: PDF and PPTX — Max {MAX_SIZE_MB}MB per
                    file. You can upload multiple files at once.
                  </p>
                  <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept=".pdf,.pptx"
                    multiple
                    onChange={handleFileInput}
                  />
                  <label
                    htmlFor="file-upload"
                    className="bg-[#272b3a] hover:bg-[#393f56] text-white text-sm font-bold px-6 py-2.5 rounded-xl cursor-pointer transition-colors shadow-lg"
                  >
                    Select Files
                  </label>
                </>
              )}

              {isDragging && (
                <div className="absolute inset-0 bg-[#5c7cff] opacity-[0.03] blur-2xl rounded-3xl -z-10" />
              )}
            </div>

            {/* Files Header & Search */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              <h2 className="text-white text-xl font-black">
                Your Files
                <span className="text-[#5c6484] text-sm font-normal ml-2">
                  ({filtered.length} {filtered.length === 1 ? "file" : "files"})
                </span>
              </h2>
              <div className="relative w-full sm:w-72">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5c6484]" />
                <input
                  type="text"
                  placeholder="Search files..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-[#12141c] border border-[#393f56] rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder:text-[#5c6484] focus:outline-none focus:border-[#5c7cff]"
                />
              </div>
            </div>

            {/* Files Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filtered.map((file) => {
                const isDeleting = deletingFileIds.has(file.id);
                return (
                  <div
                    key={file.id}
                    aria-busy={isDeleting}
                    className={`group bg-[#12141c] border border-[#272b3a] rounded-2xl p-5 transition-all w-full flex gap-4 ${
                      isDeleting
                        ? "opacity-60 cursor-wait"
                        : "hover:border-[#393f56]"
                    }`}
                  >
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      file.type === "PPTX"
                        ? "bg-orange-500/10 text-orange-400"
                        : file.type === "PDF"
                          ? "bg-red-500/10 text-red-500"
                          : file.type === "TXT"
                            ? "bg-[#0bda62]/10 text-[#0bda62]"
                            : "bg-[#5c7cff]/10 text-[#5c7cff]"
                    }`}
                  >
                    <FileType className="w-6 h-6" />
                  </div>

                  <div className="flex-1 min-w-0 flex flex-col justify-center">
                    <h3
                      className="text-white font-bold text-sm truncate mb-1 pr-2"
                      title={file.name}
                    >
                      {file.name}
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-[#5c6484]">
                      <span className="font-semibold px-1.5 py-0.5 rounded-md bg-[#272b3a]">
                        {file.type}
                      </span>
                      <span>• {file.size}</span>
                      <span>• {file.uploadDate}</span>
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-[11px]">
                      {!isDeleting &&
                        ["queued", "processing"].includes(
                          file.processingStatus,
                        ) && (
                          <RefreshCw className="w-3 h-3 text-amber-400 animate-spin" />
                        )}
                      <span
                        className={`font-bold capitalize ${
                          isDeleting
                            ? "text-red-400"
                            : file.processingStatus === "ready"
                            ? "text-emerald-400"
                            : file.processingStatus === "failed"
                              ? "text-red-400"
                              : "text-amber-400"
                        }`}
                      >
                        {isDeleting
                          ? "Deleting..."
                          : file.processingStatus === "queued"
                            ? "Preparing..."
                            : file.processingStatus === "processing"
                              ? "Converting slides..."
                              : file.processingStatus}
                      </span>
                      {file.slideCount !== null && (
                        <span className="text-[#5c6484]">
                          • {file.slideCount} slides
                        </span>
                      )}
                    </div>
                    {file.processingError && (
                      <p
                        className="mt-1 text-[11px] text-red-400 truncate"
                        title={file.processingError}
                      >
                        {file.processingError}
                      </p>
                    )}
                  </div>

                  <div
                    className={`flex gap-1 justify-center items-center transition-opacity ${
                      isDeleting ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                    }`}
                  >
                    {isDeleting ? (
                      <RefreshCw className="w-4 h-4 text-red-400 animate-spin" />
                    ) : (
                      <>
                    {file.processingStatus === "ready" && (
                      <button
                        onClick={() => void handleOpen(file)}
                        className="p-1.5 text-[#5c6484] hover:text-[#5c7cff] hover:bg-[#5c7cff]/10 rounded-lg transition-colors"
                        title="Open original presentation"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    )}
                    {file.processingStatus === "failed" && (
                      <button
                        onClick={() => void handleRetry(file)}
                        className="p-1.5 text-[#5c6484] hover:text-amber-400 hover:bg-amber-400/10 rounded-lg transition-colors"
                        title="Retry conversion"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => void handleDelete(file)}
                      className="p-1.5 text-[#5c6484] hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                      title="Delete File"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                      </>
                    )}
                  </div>
                  </div>
                );
              })}

              {filtered.length === 0 && (
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
      </PageLayout>
    </ProtectedRoute>
  );
}
