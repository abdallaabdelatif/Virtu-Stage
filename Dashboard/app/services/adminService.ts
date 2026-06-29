import { API_ENDPOINTS } from '../config/api';
import { mapAdminUser } from '../mappers/dashboardMapper';
import type { AdminUserDto } from '../types/dashboard.dto';
import type {
  UpdateManagedUserStatusRequest,
} from '../types/admin.dto';
import type { ManagedUser } from '../types/admin';
import type { BackendUserDto } from '../types/auth';
import api from '../utils/api';

export const getAdminUsers = async (): Promise<ManagedUser[]> => {
  const { data } = await api.get<AdminUserDto[]>(API_ENDPOINTS.admin.users);
  return data.map(mapAdminUser);
};

export const updateManagedUser = async (
  id: string,
  changes: { disabled: boolean },
) => {
  const request: UpdateManagedUserStatusRequest = {
    is_active: !changes.disabled,
  };
  const { data } = await api.patch<BackendUserDto>(
    API_ENDPOINTS.admin.userStatus(id),
    request,
  );
  return data;
};
