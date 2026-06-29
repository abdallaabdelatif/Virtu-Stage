export interface UserSettings {
  sessionAnalysisNotifications?: boolean;
  weeklyDigest?: boolean;
}

export interface UpdateSettingsRequest {
  sessionAnalysisNotifications?: boolean;
  weeklyDigest?: boolean;
}

export interface UpdateProfileRequest {
  first_name: string;
  last_name: string;
}

export interface AvatarUploadResponse {
  avatar_url?: string;
  url?: string;
}
