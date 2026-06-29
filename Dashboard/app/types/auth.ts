export type UserRole = 'user' | 'admin';
export type Gender = 'male' | 'female';

export interface AuthUser {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  name: string;
  email: string;
  role: UserRole;
  isActive: boolean;
  avatar: string | null;
  gender?: Gender;
}

export interface BackendUserDto {
  user_id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  gender?: Gender | null;
  role: UserRole;
  is_active: boolean;
  avatar_url?: string | null;
}

export interface AuthResult {
  success: true;
  user: AuthUser;
  token: string;
}
