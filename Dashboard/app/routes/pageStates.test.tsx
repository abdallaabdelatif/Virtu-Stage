import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as allure from 'allure-js-commons';
import { MemoryRouter } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { getDashboardStats } from '../services/dashboardService';
import { getFiles } from '../services/libraryService';
import { getAdminUsers } from '../services/adminService';
import { getSessions } from '../services/sessionService';
import type { AuthUser } from '../types/auth';
import Admin from './admin';
import Dashboard from './dashboard';
import Library from './library';
import Sessions from './sessions';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../services/dashboardService', () => ({
  getDashboardStats: vi.fn(),
}));

vi.mock('../services/sessionService', () => ({
  getSessions: vi.fn(),
}));

vi.mock('../services/libraryService', () => ({
  deleteFile: vi.fn(),
  getFileDownloadUrl: vi.fn(),
  getFiles: vi.fn(),
  retryFileProcessing: vi.fn(),
  uploadFile: vi.fn(),
}));

vi.mock('../services/adminService', () => ({
  deleteManagedUser: vi.fn(),
  getAdminUsers: vi.fn(),
  updateManagedUser: vi.fn(),
}));

vi.mock('../components/UserDashboard', () => ({
  UserDashboard: ({
    name,
    data,
  }: {
    name: string;
    data: { totalSessions: number };
  }) => (
    <div>
      User dashboard for {name}: {data.totalSessions}
    </div>
  ),
}));

vi.mock('../components/AdminDashboard', () => ({
  AdminDashboard: ({
    name,
    data,
  }: {
    name: string;
    data: { totalUsers: number };
  }) => (
    <div>
      Admin dashboard for {name}: {data.totalUsers}
    </div>
  ),
}));

const mockedUseAuth = vi.mocked(useAuth);
const mockedGetDashboardStats = vi.mocked(getDashboardStats);
const mockedGetSessions = vi.mocked(getSessions);
const mockedGetFiles = vi.mocked(getFiles);
const mockedGetAdminUsers = vi.mocked(getAdminUsers);

const user: AuthUser = {
  id: 'user-1',
  username: 'sara',
  firstName: 'Sara',
  lastName: 'Ahmed',
  name: 'Sara Ahmed',
  email: 'sara@example.com',
  role: 'user',
  isActive: true,
  avatar: null,
  gender: 'female',
};

function renderPage(element: React.ReactElement) {
  return render(<MemoryRouter>{element}</MemoryRouter>);
}

describe('page states', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseAuth.mockReturnValue({
      user,
      isAuthenticated: true,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
    });
  });

  it('renders dashboard data for authenticated users', async () => {
    await allure.feature('Frontend Pages');
    await allure.story('Dashboard data state');

    mockedGetDashboardStats.mockResolvedValue({
      totalSessions: 3,
      analyzedSessions: 2,
      avgScore: 82,
      improvementRate: null,
      progressData: [],
      voiceMotionData: [],
    });

    renderPage(<Dashboard />);

    expect(
      await screen.findByText(/User dashboard for Sara Ahmed: 3/),
    ).toBeInTheDocument();
    expect(mockedGetDashboardStats).toHaveBeenCalledWith('user');
  });

  it('renders sessions empty state', async () => {
    await allure.feature('Frontend Pages');
    await allure.story('Sessions empty state');

    mockedGetSessions.mockResolvedValue([]);

    renderPage(<Sessions />);

    expect(await screen.findByText('No VR sessions yet')).toBeInTheDocument();
  });

  it('validates unsupported library uploads before calling upload API', async () => {
    await allure.feature('Frontend Pages');
    await allure.story('Library upload validation');

    mockedGetFiles.mockResolvedValue([]);

    renderPage(<Library />);

    await screen.findByText('No files yet');
    const input = screen.getByLabelText('Select Files');
    fireEvent.change(input, {
      target: {
        files: [new File(['hello'], 'notes.txt', { type: 'text/plain' })],
      },
    });

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'unsupported type',
    );
  });

  it('renders admin users and filters search results', async () => {
    await allure.feature('Frontend Pages');
    await allure.story('Admin user management');

    mockedGetAdminUsers.mockResolvedValue([
      {
        id: 'admin-1',
        name: 'Admin User',
        email: 'admin@example.com',
        role: 'admin',
        sessions: 0,
        joinedAt: 'Jun 30, 2026',
        disabled: false,
      },
      {
        id: 'user-1',
        name: 'Regular User',
        email: 'regular@example.com',
        role: 'user',
        sessions: 4,
        joinedAt: 'Jun 30, 2026',
        disabled: false,
      },
    ]);

    renderPage(<Admin />);

    expect(await screen.findByText('Regular User')).toBeInTheDocument();
    expect(screen.queryByText('Admin User')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Search users'), {
      target: { value: 'missing' },
    });

    expect(screen.getByText('No matching users')).toBeInTheDocument();
  });
});
