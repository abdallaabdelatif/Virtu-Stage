import {
  type RouteConfig,
  index,
  layout,
  route,
} from '@react-router/dev/routes';

export default [
  index('routes/home.tsx'),
  route('register', 'routes/register.tsx'),
  route('forgot-password', 'routes/forgot-password.tsx'),
  route('reset-password', 'routes/reset-password.tsx'),

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

  route('*', 'routes/not-found.tsx'),
] satisfies RouteConfig;
