import { API_ENDPOINTS } from '../config/api';
import type {
  AvatarUploadResponse,
  UpdateProfileRequest,
  UpdateSettingsRequest,
  UserSettings,
} from '../types/settings';
import type { BackendUserDto } from '../types/auth';
import api from '../utils/api';

export const getSettings = async () => {
  const { data } = await api.get<UserSettings>(API_ENDPOINTS.settings.me);
  return data;
};

export const saveSettings = async (settings: UpdateSettingsRequest) => {
  const { data } = await api.patch<UserSettings>(
    API_ENDPOINTS.settings.me,
    settings,
  );
  return data;
};

export const updateUserProfile = async (
  firstName: string,
  lastName: string,
) => {
  const request: UpdateProfileRequest = {
    first_name: firstName,
    last_name: lastName,
  };
  const { data } = await api.patch<BackendUserDto>(
    API_ENDPOINTS.settings.profile,
    request,
  );
  return data;
};

export const deleteAccount = async () => {
  await api.delete(API_ENDPOINTS.settings.account);
};

export const uploadAvatar = async (file: File): Promise<string> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<AvatarUploadResponse>(
    API_ENDPOINTS.settings.avatar,
    formData,
  );
  const avatarUrl = data.avatar_url ?? data.url;
  if (!avatarUrl) throw new Error('Avatar URL missing from response');
  return avatarUrl;
};
