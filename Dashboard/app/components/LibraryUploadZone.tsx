import type { DragEventHandler } from 'react';
import { UploadCloud } from 'lucide-react';

export interface UploadProgress {
  id: string;
  name: string;
  progress: number;
}

interface LibraryUploadZoneProps {
  isDragging: boolean;
  uploads: UploadProgress[];
  maxSizeMb: number;
  onDragEnter: DragEventHandler<HTMLDivElement>;
  onDragLeave: DragEventHandler<HTMLDivElement>;
  onDragOver: DragEventHandler<HTMLDivElement>;
  onDrop: DragEventHandler<HTMLDivElement>;
  onFileInput: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function LibraryUploadZone({
  isDragging,
  uploads,
  maxSizeMb,
  onDragEnter,
  onDragLeave,
  onDragOver,
  onDrop,
  onFileInput,
}: LibraryUploadZoneProps) {
  const isUploading = uploads.length > 0;

  return (
    <div
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDragOver={onDragOver}
      onDrop={onDrop}
      className={`relative mb-8 flex w-full flex-col items-center justify-center rounded-3xl border-2 border-dashed transition-all duration-300 ease-out ${
        isUploading ? 'h-auto px-6 py-6' : 'h-64 px-4'
      } ${
        isDragging
          ? 'border-brand bg-brand/5'
          : 'border-border-strong bg-surface hover:border-muted hover:bg-panel'
      }`}
    >
      {isUploading ? (
        <div className="w-full max-w-md space-y-4" aria-live="polite">
          <div className="mb-2 flex items-center gap-3">
            <UploadCloud
              aria-hidden="true"
              className="h-6 w-6 animate-bounce text-brand-soft"
            />
            <p className="font-bold text-white">
              Uploading {uploads.length} file{uploads.length > 1 ? 's' : ''}...
            </p>
          </div>
          {uploads.map((file) => (
            <div key={file.id}>
              <div className="mb-1 flex justify-between gap-3">
                <p className="truncate text-xs text-secondary">{file.name}</p>
                <p className="shrink-0 text-xs font-bold text-brand-soft">
                  {file.progress}%
                </p>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-elevated">
                <div
                  role="progressbar"
                  aria-label={`Uploading ${file.name}`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={file.progress}
                  className="h-full rounded-full bg-brand transition-all duration-200"
                  style={{ width: `${file.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <>
          <div
            className={`mb-4 flex h-16 w-16 items-center justify-center rounded-full transition-colors ${
              isDragging
                ? 'bg-brand/20 text-brand-soft'
                : 'bg-elevated text-secondary'
            }`}
          >
            <UploadCloud aria-hidden="true" className="h-8 w-8" />
          </div>
          <h2 className="mb-2 text-center text-lg font-black tracking-tight text-white">
            Click or drag files to upload
          </h2>
          <p className="mb-6 max-w-md text-center text-sm text-muted">
            Supported: PDF and PPTX — Max {maxSizeMb}MB per file. You can upload
            multiple files at once.
          </p>
          <input
            type="file"
            id="file-upload"
            className="peer sr-only"
            accept=".pdf,.pptx"
            multiple
            onChange={onFileInput}
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer rounded-xl bg-elevated px-6 py-2.5 text-sm font-bold text-white shadow-lg transition-colors hover:bg-border-strong peer-focus-visible:ring-2 peer-focus-visible:ring-brand-soft peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-surface"
          >
            Select Files
          </label>
        </>
      )}

      {isDragging && (
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-10 rounded-3xl bg-brand opacity-[0.03] blur-2xl"
        />
      )}
    </div>
  );
}
