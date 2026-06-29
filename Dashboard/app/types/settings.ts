export interface UpdateProfileRequest {
  first_name: string;
  last_name: string;
}

export interface AvatarUploadResponse {
  avatar_url?: string;
  url?: string;
}
