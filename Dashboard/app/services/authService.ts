import { API_ENDPOINTS } from '../config/api';
import { mapBackendUser } from '../mappers/userMapper';
import type { AuthResult, Gender } from '../types/auth';
import type {
  AuthResponseDto,
  ChangePasswordRequestDto,
  CurrentUserResponseDto,
  ForgotPasswordRequestDto,
  LoginRequestDto,
  MessageResponseDto,
  RegisterRequestDto,
  ResetPasswordRequestDto,
} from '../types/auth.dto';
import api from '../utils/api';

export const loginCall = async (
  usernameOrEmail: string,
  password: string,
): Promise<AuthResult> => {
  const request: LoginRequestDto = {
    username_or_email: usernameOrEmail.trim(),
    password,
  };
  const { data } = await api.post<AuthResponseDto>(
    API_ENDPOINTS.auth.login,
    request,
  );
  const token = data.access_token ?? data.token;
  if (!token) throw new Error('Access token missing from login response');
  return {
    success: true,
    token,
    user: mapBackendUser(data.user),
  };
};

export const registerCall = async (
  username: string,
  firstName: string,
  lastName: string,
  gender: Gender,
  email: string,
  password: string,
): Promise<AuthResult> => {
  const request: RegisterRequestDto = {
    username,
    email,
    password,
    first_name: firstName,
    last_name: lastName,
    gender,
  };
  const { data } = await api.post<AuthResponseDto>(
    API_ENDPOINTS.auth.register,
    request,
  );
  const token = data.access_token ?? data.token;
  if (!token)
    throw new Error('Access token missing from registration response');
  return {
    success: true,
    token,
    user: mapBackendUser(data.user),
  };
};

export const verifySessionCall = async () => {
  const { data } = await api.get<CurrentUserResponseDto>(API_ENDPOINTS.auth.me);
  return mapBackendUser('user' in data ? data.user : data);
};

export const forgotPasswordCall = async (email: string) => {
  const request: ForgotPasswordRequestDto = {
    email: email.trim().toLowerCase(),
  };
  const { data } = await api.post<MessageResponseDto>(
    API_ENDPOINTS.auth.forgotPassword,
    request,
  );
  return data;
};

export const resetPasswordCall = async (token: string, newPassword: string) => {
  const request: ResetPasswordRequestDto = {
    token,
    new_password: newPassword,
  };
  const { data } = await api.post<MessageResponseDto>(
    API_ENDPOINTS.auth.resetPassword,
    request,
  );
  return data;
};

export const changePasswordCall = async (
  currentPassword: string,
  newPassword: string,
) => {
  const request: ChangePasswordRequestDto = {
    current_password: currentPassword,
    new_password: newPassword,
  };
  const { data } = await api.patch<MessageResponseDto>(
    API_ENDPOINTS.auth.changePassword,
    request,
  );
  return data;
};
