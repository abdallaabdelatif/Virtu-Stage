import type { UserRole } from './auth';

export interface ManagedUser {
  id: string;
  name: string;
  email: string;
  sessions: number;
  joinedAt: string;
  role: UserRole;
  disabled: boolean;
}

export interface PlatformActivity {
  id: string;
  type: string;
  icon: string;
  title: string;
  desc: string;
  time: string;
}
