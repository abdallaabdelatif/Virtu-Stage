import { ExternalLink, FileType, RefreshCw, Trash2 } from 'lucide-react';
import type { LibraryFile } from '../types/library';

interface LibraryFileCardProps {
  file: LibraryFile;
  isDeleting: boolean;
  onDelete: (file: LibraryFile) => void;
  onOpen: (file: LibraryFile) => void;
  onRetry: (file: LibraryFile) => void;
}

const fileTone = (type: LibraryFile['type']) => {
  if (type === 'PPTX') return 'bg-orange-500/10 text-orange-400';
  if (type === 'PDF') return 'bg-red-500/10 text-red-400';
  if (type === 'TXT') return 'bg-success/10 text-success';
  return 'bg-brand/10 text-brand-soft';
};

export function LibraryFileCard({
  file,
  isDeleting,
  onDelete,
  onOpen,
  onRetry,
}: LibraryFileCardProps) {
  const isProcessing = ['queued', 'processing'].includes(file.processingStatus);
  const statusLabel = isDeleting
    ? 'Deleting...'
    : file.processingStatus === 'queued'
      ? 'Preparing...'
      : file.processingStatus === 'processing'
        ? 'Converting slides...'
        : file.processingStatus;
  const statusTone =
    isDeleting || file.processingStatus === 'failed'
      ? 'text-red-400'
      : file.processingStatus === 'ready'
        ? 'text-emerald-400'
        : 'text-amber-400';

  return (
    <article
      aria-busy={isDeleting}
      className={`group flex w-full gap-4 rounded-2xl border border-border-subtle bg-surface p-5 transition-all ${
        isDeleting ? 'cursor-wait opacity-60' : 'hover:border-border-strong'
      }`}
    >
      <div
        className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${fileTone(file.type)}`}
      >
        <FileType aria-hidden="true" className="h-6 w-6" />
      </div>

      <div className="flex min-w-0 flex-1 flex-col justify-center">
        <h3
          className="mb-1 truncate pr-2 text-sm font-bold text-white"
          title={file.name}
        >
          {file.name}
        </h3>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
          <span className="rounded-md bg-elevated px-1.5 py-0.5 font-semibold">
            {file.type}
          </span>
          <span>• {file.size}</span>
          <span>• {file.uploadDate}</span>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px]">
          {!isDeleting && isProcessing && (
            <RefreshCw
              aria-hidden="true"
              className="h-3 w-3 animate-spin text-amber-400"
            />
          )}
          <span className={`font-bold capitalize ${statusTone}`}>
            {statusLabel}
          </span>
          {file.slideCount !== null && (
            <span className="text-muted">• {file.slideCount} slides</span>
          )}
        </div>
        {file.processingError && (
          <p
            className="mt-1 truncate text-[11px] text-red-400"
            title={file.processingError}
          >
            {file.processingError}
          </p>
        )}
      </div>

      <div
        className={`flex items-center justify-center gap-1 transition-opacity ${
          isDeleting
            ? 'opacity-100'
            : 'opacity-100 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100'
        }`}
      >
        {isDeleting ? (
          <RefreshCw
            aria-label="Deleting file"
            className="h-4 w-4 animate-spin text-red-400"
          />
        ) : (
          <>
            {file.processingStatus === 'ready' && (
              <IconAction
                label={`Open ${file.name}`}
                onClick={() => onOpen(file)}
                tone="hover:bg-brand/10 hover:text-brand-soft"
              >
                <ExternalLink aria-hidden="true" className="h-4 w-4" />
              </IconAction>
            )}
            {file.processingStatus === 'failed' && (
              <IconAction
                label={`Retry processing ${file.name}`}
                onClick={() => onRetry(file)}
                tone="hover:bg-amber-400/10 hover:text-amber-400"
              >
                <RefreshCw aria-hidden="true" className="h-4 w-4" />
              </IconAction>
            )}
            <IconAction
              label={`Delete ${file.name}`}
              onClick={() => onDelete(file)}
              tone="hover:bg-red-400/10 hover:text-red-400"
            >
              <Trash2 aria-hidden="true" className="h-4 w-4" />
            </IconAction>
          </>
        )}
      </div>
    </article>
  );
}

function IconAction({
  children,
  label,
  onClick,
  tone,
}: {
  children: React.ReactNode;
  label: string;
  onClick: () => void;
  tone: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className={`rounded-lg p-1.5 text-muted transition-colors ${tone}`}
    >
      {children}
    </button>
  );
}
