import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import {
  LayoutDashboard,
  PlaySquare,
  BarChart2,
  BookOpen,
  Settings,
  LogOut,
  Menu,
  X,
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
  const mobileDrawerRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  const isAdmin = user?.role === 'admin';
  const navItems = isAdmin ? adminNavItems : userNavItems;

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path: string) => {
    if (path === '/analytics') {
      return (
        location.pathname === path ||
        location.pathname.startsWith('/session-analytics/')
      );
    }
    if (path === '/sessions') {
      return (
        location.pathname === path || location.pathname.startsWith('/session/')
      );
    }
    return location.pathname === path;
  };

  useEffect(() => {
    if (!sidebarOpen) return;

    const previousOverflow = document.body.style.overflow;
    const menuButton = menuButtonRef.current;
    document.body.style.overflow = 'hidden';

    const drawer = mobileDrawerRef.current;
    const focusableSelector =
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const focusable = () =>
      Array.from(
        drawer?.querySelectorAll<HTMLElement>(focusableSelector) ?? [],
      );

    focusable()[0]?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSidebarOpen(false);
        return;
      }
      if (event.key !== 'Tab') return;

      const elements = focusable();
      if (elements.length === 0) return;
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
      menuButton?.focus();
    };
  }, [sidebarOpen]);

  const renderSidebarContent = (mobile = false) => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center h-[76px] gap-3 px-4 border-b border-border-subtle">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand/10 ring-1 ring-brand/20">
          <VirtuStageLogo className="h-10 w-10 object-contain" />
        </div>
        <div>
          <p className="text-[#d9d9d9] font-bold text-sm">VirtuStage</p>
          <p className="text-muted text-xs">
            {isAdmin ? 'Admin Console' : 'AI VR Training'}
          </p>
        </div>
        {mobile && (
          <button
            type="button"
            aria-label="Close navigation menu"
            onClick={() => setSidebarOpen(false)}
            className="ml-auto rounded-lg p-2 text-secondary hover:bg-white/5 hover:text-white"
          >
            <X aria-hidden="true" className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {/* Section label for admin */}
        {isAdmin && (
          <p className="text-muted text-xs font-bold uppercase tracking-wider px-3 pb-2">
            Admin
          </p>
        )}

        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            onClick={() => setSidebarOpen(false)}
            aria-current={isActive(item.path) ? 'page' : undefined}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
              isActive(item.path)
                ? 'bg-brand text-brand-contrast'
                : 'text-secondary hover:bg-white/5 hover:text-white'
            }`}
          >
            {item.icon}
            {item.label}
          </Link>
        ))}
      </nav>

      {/* User Info + Logout */}
      <div className="px-3 py-4 border-t border-border-subtle">
        <Link
          to="/settings"
          aria-label="Open profile settings"
          className="flex items-center gap-3 px-3 py-2 rounded-xl bg-[#121610] mb-2 hover:bg-[#1a2117] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#c1ff72]/70 transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-brand/30 flex items-center justify-center text-brand-soft font-bold text-sm flex-shrink-0 overflow-hidden">
            {user?.avatar ? (
              <img
                src={user.avatar}
                alt={`${user?.name ?? 'User'} avatar`}
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
            <p className="text-muted text-xs truncate">{user?.email}</p>
          </div>
        </Link>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-secondary hover:bg-red-500/10 hover:text-red-400 transition-all"
        >
          <LogOut className="w-5 h-5" />
          Logout
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_0%_100%,rgba(193,255,114,0.12),transparent_34rem),linear-gradient(115deg,#10130f_0%,#111410_48%,#062815_100%)] text-white flex">
      <a
        href="#main-content"
        className="sr-only z-[200] rounded-lg bg-brand px-4 py-2 text-brand-contrast focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        Skip to main content
      </a>
      {/* Desktop Sidebar */}
      <aside
        aria-label="Primary navigation"
        className="hidden lg:flex flex-col w-56 bg-sidebar border-r border-border-subtle fixed h-full z-20"
      >
        {renderSidebarContent()}
      </aside>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-30 flex">
          <div
            ref={mobileDrawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation menu"
            className="w-64 max-w-[85vw] bg-sidebar border-r border-border-subtle flex flex-col shadow-2xl"
          >
            {renderSidebarContent(true)}
          </div>
          <button
            type="button"
            aria-label="Close navigation menu"
            className="flex-1 bg-black/50"
            onClick={() => setSidebarOpen(false)}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 lg:ml-56 flex flex-col min-h-screen">
        {/* Top Bar */}
        <header className="sticky top-0 z-10 h-[76px] flex items-center justify-between px-4 sm:px-6 border-b border-border-subtle bg-canvas/80 backdrop-blur-sm">
          <button
            ref={menuButtonRef}
            type="button"
            aria-label="Open navigation menu"
            aria-expanded={sidebarOpen}
            className="lg:hidden p-2 rounded-xl hover:bg-white/5 transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu aria-hidden="true" className="w-5 h-5 text-secondary" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <Link
              to="/settings"
              aria-label="Open profile settings"
              className="w-8 h-8 rounded-full bg-brand/30 flex items-center justify-center text-brand-soft font-bold text-sm overflow-hidden flex-shrink-0"
              title="Go to Profile Settings"
            >
              {user?.avatar ? (
                <img
                  src={user.avatar}
                  alt={`${user?.name ?? 'User'} avatar`}
                  className="w-full h-full object-cover rounded-full"
                />
              ) : (
                user?.name?.charAt(0).toUpperCase()
              )}
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <main id="main-content" className="flex-1 p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
