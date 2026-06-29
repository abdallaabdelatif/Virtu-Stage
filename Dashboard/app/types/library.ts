export interface LibraryFile {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadDate: string;
  processingStatus: PresentationProcessingStatus;
  slideCount: number | null;
  processingError: string | null;
}

export type PresentationProcessingStatus =
  | 'queued'
  | 'processing'
  | 'ready'
  | 'failed';

export interface BackendLibraryFileDto {
  file_id: string;
  original_name: string;
  content_type: string;
  size_bytes: number;
  upload_status: 'ready';
  processing_status: PresentationProcessingStatus;
  slide_count: number | null;
  processing_error: string | null;
  created_at: string;
}

export interface FileDownloadDto {
  url: string;
  expires_at: string;
}

export interface PresentationSlideDto {
  number: number;
  width: number;
  height: number;
  size_bytes: number;
  url: string;
  expires_at: string;
}

export interface PresentationSlidesManifestDto {
  file_id: string;
  original_name: string;
  processing_status: 'ready';
  slide_count: number;
  slides: PresentationSlideDto[];
}
