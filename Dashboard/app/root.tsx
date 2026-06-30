import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from 'react-router';

import type { Route } from './+types/root';
import './app.css';

import { AuthProvider } from './context/AuthContext'; // ADDED THIS

export const meta: Route.MetaFunction = () => [
  { title: 'VirtuStage' },
  {
    name: 'description',
    content: 'AI-enhanced VR presentation training and performance analytics.',
  },
];

export const links: Route.LinksFunction = () => [
  { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
  {
    rel: 'preconnect',
    href: 'https://fonts.gstatic.com',
    crossOrigin: 'anonymous',
  },
  {
    rel: 'stylesheet',
    href: 'https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap',
  },
  { rel: 'icon', type: 'image/png', href: '/virtustage-icon.png' },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = 'Oops!';
  let details = 'An unexpected error occurred.';
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? '404' : 'Error';
    details =
      error.status === 404
        ? 'The requested page could not be found.'
        : error.statusText || details;
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message;
    stack = error.stack;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-canvas px-6 py-16 text-center text-white">
      <p className="mb-2 text-sm font-bold uppercase tracking-[0.2em] text-brand-soft">
        VirtuStage
      </p>
      <h1 className="text-4xl font-black">{message}</h1>
      <p className="mt-3 max-w-xl text-secondary">{details}</p>
      {stack && (
        <pre className="mt-8 w-full max-w-4xl overflow-x-auto rounded-2xl border border-border-subtle bg-surface p-4 text-left text-sm">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  );
}
