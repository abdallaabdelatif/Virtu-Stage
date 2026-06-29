import type { BackendLibraryFileDto, LibraryFile } from '../types/library';

const formatSize = (bytes: number): string => {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

export const mapLibraryFile = (file: BackendLibraryFileDto): LibraryFile => ({
  id: file.file_id,
  name: file.original_name,
  type: file.original_name.split('.').pop()?.toUpperCase() || 'FILE',
  size: formatSize(file.size_bytes),
  uploadDate: new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(file.created_at)),
  processingStatus: file.processing_status,
  slideCount: file.slide_count,
  processingError: file.processing_error,
});
