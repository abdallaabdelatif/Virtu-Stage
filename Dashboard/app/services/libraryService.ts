import { API_ENDPOINTS } from '../config/api';
import { mapLibraryFile } from '../mappers/libraryMapper';
import type {
  BackendLibraryFileDto,
  FileDownloadDto,
  LibraryFile,
  PresentationSlidesManifestDto,
} from '../types/library';
import api from '../utils/api';

export const getFiles = async (): Promise<LibraryFile[]> => {
  const { data } = await api.get<BackendLibraryFileDto[]>(
    API_ENDPOINTS.files.list,
  );
  return data.map(mapLibraryFile);
};

export const uploadFile = async (
  file: File,
  onProgress?: (progress: number) => void,
): Promise<LibraryFile> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<BackendLibraryFileDto>(
    API_ENDPOINTS.files.upload,
    formData,
    {
      timeout: 120_000,
      onUploadProgress: (event) => {
        if (event.total) {
          onProgress?.(Math.round((event.loaded * 100) / event.total));
        }
      },
    },
  );
  return mapLibraryFile(data);
};

export const deleteFile = async (id: string) => {
  await api.delete(API_ENDPOINTS.files.delete(id), { timeout: 120_000 });
};

export const getFileDownloadUrl = async (id: string): Promise<string> => {
  const { data } = await api.get<FileDownloadDto>(
    API_ENDPOINTS.files.download(id),
  );
  return data.url;
};

export const retryFileProcessing = async (id: string): Promise<LibraryFile> => {
  const { data } = await api.post<BackendLibraryFileDto>(
    API_ENDPOINTS.files.retry(id),
  );
  return mapLibraryFile(data);
};

export const getPresentationSlides = async (
  id: string,
): Promise<PresentationSlidesManifestDto> => {
  const { data } = await api.get<PresentationSlidesManifestDto>(
    API_ENDPOINTS.files.slides(id),
  );
  return data;
};
