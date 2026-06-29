import type { BackendUserDto, Gender } from "./auth";

export interface LoginRequestDto {
  username_or_email: string;
  password: string;
}

export interface RegisterRequestDto {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  gender: Gender;
}

export interface AuthResponseDto {
  access_token?: string;
  token?: string;
  user: BackendUserDto;
}

export type CurrentUserResponseDto = BackendUserDto | { user: BackendUserDto };

export interface ForgotPasswordRequestDto {
  email: string;
}

export interface ResetPasswordRequestDto {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequestDto {
  current_password: string;
  new_password: string;
}

export interface MessageResponseDto {
  message: string;
}
