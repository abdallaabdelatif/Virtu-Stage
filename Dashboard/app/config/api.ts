export const API_ENDPOINTS = {
  auth: {
    login: '/api/auth/login',
    register: '/api/auth/register',
    me: '/api/auth/me',
    forgotPassword: '/api/auth/forgot-password',
    resetPassword: '/api/auth/reset-password',
    changePassword: '/api/users/me/password',
  },
  sessions: {
    mine: '/api/sessions/me',
    detail: (id: string) => `/api/sessions/${id}`,
    report: (id: string) => `/api/sessions/${id}/report`,
    status: (id: string) => `/api/sessions/${id}/status`,
  },
  dashboard: {
    user: '/api/dashboard/me',
    admin: '/api/admin/dashboard',
  },
  files: {
    list: '/api/files',
    upload: '/api/files',
    download: (id: string) => `/api/files/${id}/download`,
    status: (id: string) => `/api/files/${id}/status`,
    slides: (id: string) => `/api/files/${id}/slides`,
    retry: (id: string) => `/api/files/${id}/retry`,
    delete: (id: string) => `/api/files/${id}`,
  },
  settings: {
    profile: '/api/users/me',
    avatar: '/api/users/me/avatar',
    account: '/api/users/me',
  },
  admin: {
    data: '/api/admin',
    users: '/api/admin/users',
    userStatus: (id: string) => `/api/admin/users/${id}/status`,
    deleteUser: (id: string) => `/api/admin/users/${id}`,
  },
} as const;
