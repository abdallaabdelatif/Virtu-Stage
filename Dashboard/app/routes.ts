import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  // ── Auth ──────────────────────────────
  index("routes/home.tsx"), // / → Login
  route("register", "routes/register.tsx"), // /register
  route("forgot-password", "routes/forgot-password.tsx"), // /forgot-password
  route("reset-password", "routes/reset-password.tsx"), // /reset-password?token=...

  // ── Main Dashboard ────────────────────
  route("dashboard", "routes/dashboard.tsx"), // /dashboard
  route("analytics", "routes/analytics.tsx"), // /analytics

  // ── Sessions ──────────────────────────
  route("sessions", "routes/sessions.tsx"), // /sessions
  route("session/:id", "routes/session.$id.tsx"), // /session/:id → redirects to analytics
  route("session-analytics/:id", "routes/session.analytics.tsx"), // /session-analytics/1 → Detailed analysis

  // ── Content ───────────────────────────
  route("library", "routes/library.tsx"), // /library → Training Materials

  // ── User ──────────────────────────────
  route("settings", "routes/settings.tsx"), // /settings

  // ── Admin ─────────────────────────────
  route("admin", "routes/admin.tsx"), // /admin

  // ── Error Pages ──
  route("*", "routes/not-found.tsx"),
] satisfies RouteConfig;
