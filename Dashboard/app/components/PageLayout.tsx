import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import {
  LayoutDashboard,
  PlaySquare,
  BarChart2,
  BookOpen,
  Settings,
  Shield,
  LogOut,
  Menu,
  Bell,
  Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { VirtuStageLogo } from './icons';

// ── Regular User Nav ──────────────────────────────
const userNavItems = [
  {
    label: 'Dashboard',
    icon: <LayoutDashboard className="w-5 h-5" />,
    path: '/dashboard',
  },
  {
    label: 'Sessions',
    icon: <PlaySquare className="w-5 h-5" />,
    path: '/sessions',
  },
  {
    label: 'Analytics',
    icon: <BarChart2 className="w-5 h-5" />,
    path: '/analytics',
  },
  {
    label: 'Library',
    icon: <BookOpen className="w-5 h-5" />,
    path: '/library',
  },
  {
    label: 'Settings',
    icon: <Settings className="w-5 h-5" />,
    path: '/settings',
  },
];

// ── Admin Nav ─────────────────────────────────────
const adminNavItems = [
  {
    label: 'Dashboard',
    icon: <LayoutDashboard className="w-5 h-5" />,
    path: '/dashboard',
  },
  {
    label: 'User Management',
    icon: <Users className="w-5 h-5" />,
    path: '/admin',
  },
  {
    label: 'Settings',
    icon: <Settings className="w-5 h-5" />,
    path: '/settings',
  },
];

interface PageLayoutProps {
  children: React.ReactNode;
}

export function PageLayout({ children }: PageLayoutProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isAdmin = user?.role === 'admin';
  const navItems = isAdmin ? adminNavItems : userNavItems;

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path: string) => location.pathname === path;

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center h-[76px] gap-3 px-4 border-b border-[#272b3a]">
        <div className="w-14 h-14 rounded-xl bg-[#5c7cff]/20 flex items-center justify-center">
          <VirtuStageLogo className="w-14 h-14 text-[#5c7cff]" />
        </div>
        <div>
          <p className="text-white font-bold text-sm">VirtuStage</p>
          <p className="text-[#5c6484] text-xs">
            {isAdmin ? 'Admin Console' : 'AI VR Training'}
          </p>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {/* Section label for admin */}
        {isAdmin && (
          <p className="text-[#5c6484] text-xs font-bold uppercase tracking-wider px-3 pb-2">
            Admin
          </p>
        )}

        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            onClick={() => setSidebarOpen(false)}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
              isActive(item.path)
                ? 'bg-[#5c7cff] text-white'
                : 'text-[#9aa1bc] hover:bg-white/5 hover:text-white'
            }`}
          >
            {item.icon}
            {item.label}
          </Link>
        ))}
      </nav>

      {/* User Info + Logout */}
      <div className="px-3 py-4 border-t border-[#272b3a]">
        <Link
          to="/settings"
          aria-label="Open profile settings"
          className="flex items-center gap-3 px-3 py-2 rounded-xl bg-[#12141c] mb-2 hover:bg-[#1b1d28] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c7cff]/70 transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-[#5c7cff]/30 flex items-center justify-center text-[#5c7cff] font-bold text-sm flex-shrink-0 overflow-hidden">
            {user?.avatar ? (
              <img
                src={user.avatar}
                alt="avatar"
                className="w-full h-full object-cover rounded-full"
              />
            ) : (
              user?.name?.charAt(0).toUpperCase()
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-semibold truncate">
              {user?.name}
            </p>
            <p className="text-[#5c6484] text-xs truncate">{user?.email}</p>
          </div>
        </Link>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-[#9aa1bc] hover:bg-red-500/10 hover:text-red-400 transition-all"
        >
          <LogOut className="w-5 h-5" />
          Logout
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0f1323] text-white flex">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-56 bg-[#0d0f1c] border-r border-[#272b3a] fixed h-full z-20">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-30 flex">
          <div className="w-56 bg-[#0d0f1c] border-r border-[#272b3a] flex flex-col">
            <SidebarContent />
          </div>
          <div
            className="flex-1 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 lg:ml-56 flex flex-col min-h-screen">
        {/* Top Bar */}
        <header className="sticky top-0 z-10 h-[76px] flex items-center justify-between px-6 border-b border-[#272b3a] bg-[#0f1323]/80 backdrop-blur-sm">
          <button
            className="lg:hidden p-2 rounded-xl hover:bg-white/5 transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5 text-[#9aa1bc]" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label="Open notifications"
              className="relative p-2 rounded-xl hover:bg-white/5 transition-colors"
            >
              <Bell className="w-5 h-5 text-[#9aa1bc]" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#5c7cff] rounded-full" />
            </button>
            <Link
              to="/settings"
              className="w-8 h-8 rounded-full bg-[#5c7cff]/30 flex items-center justify-center text-[#5c7cff] font-bold text-sm overflow-hidden flex-shrink-0"
              title="Go to Profile Settings"
            >
              {user?.avatar ? (
                <img
                  src={user.avatar}
                  alt="avatar"
                  className="w-full h-full object-cover rounded-full"
                />
              ) : (
                user?.name?.charAt(0).toUpperCase()
              )}
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
