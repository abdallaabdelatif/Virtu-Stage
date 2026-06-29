import {
  type RouteConfig,
  index,
  layout,
  route,
} from '@react-router/dev/routes';

export default [
  // ── Auth ──────────────────────────────
  index('routes/home.tsx'), // / → Login
  route('register', 'routes/register.tsx'), // /register
  route('forgot-password', 'routes/forgot-password.tsx'), // /forgot-password
  route('reset-password', 'routes/reset-password.tsx'), // /reset-password?token=...

  layout('routes/protected-layout.tsx', [
    route('dashboard', 'routes/dashboard.tsx'),
    route('settings', 'routes/settings.tsx'),
  ]),

  layout('routes/user-layout.tsx', [
    route('analytics', 'routes/analytics.tsx'),
    route('sessions', 'routes/sessions.tsx'),
    route('session/:id', 'routes/session.$id.tsx'),
    route('session-analytics/:id', 'routes/session.analytics.tsx'),
    route('library', 'routes/library.tsx'),
  ]),

  layout('routes/admin-layout.tsx', [route('admin', 'routes/admin.tsx')]),

  // ── Error Pages ──
  route('*', 'routes/not-found.tsx'),
] satisfies RouteConfig;
