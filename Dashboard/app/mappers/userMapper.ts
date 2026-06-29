import type { AuthUser, BackendUserDto } from '../types/auth';

export function mapBackendUser(dto: BackendUserDto): AuthUser {
  return {
    id: dto.user_id,
    username: dto.username,
    firstName: dto.first_name,
    lastName: dto.last_name,
    name: `${dto.first_name} ${dto.last_name}`.trim(),
    email: dto.email,
    role: dto.role,
    isActive: dto.is_active,
    avatar: dto.avatar_url ?? null,
    gender: dto.gender ?? undefined,
  };
}
