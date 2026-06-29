import { API_ENDPOINTS } from '../config/api';
import {
  mapAdminDashboard,
  mapUserDashboard,
} from '../mappers/dashboardMapper';
import type {
  AdminDashboardDto,
  UserDashboardDto,
} from '../types/dashboard.dto';
import type {
  AdminDashboardData,
  UserDashboardData,
} from '../types/dashboard';
import api from '../utils/api';

export function getDashboardStats(role: 'admin'): Promise<AdminDashboardData>;
export function getDashboardStats(role?: 'user'): Promise<UserDashboardData>;
export async function getDashboardStats(role: 'admin' | 'user' = 'user') {
  if (role === 'admin') {
    const { data } = await api.get<AdminDashboardDto>(
      API_ENDPOINTS.dashboard.admin,
    );
    return mapAdminDashboard(data);
  }

  const { data } = await api.get<UserDashboardDto>(API_ENDPOINTS.dashboard.user);
  return mapUserDashboard(data);
}
