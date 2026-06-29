# VirtuStage Dashboard Frontend

React frontend for the VirtuStage AI/VR training dashboard.

This repository is intended to contain the frontend only. The browser connects
to the Central Backend API, and the Central Backend communicates with the
backend services/CRUD layer.

```txt
Frontend Dashboard
  -> Central Backend API
      -> CRUD Backend
          -> PostgreSQL
```

## Tech Stack

- React
- React Router
- TypeScript
- Tailwind CSS
- Axios
- Recharts
- SweetAlert2

## Local Setup

Install dependencies:

```bash
npm install
```

Create a local environment file:

```bash
cp .env.example .env
```

For local development, use:

```env
VITE_API_URL=http://localhost:9000
```

Start the frontend:

```bash
npm run dev
```

Open:

```txt
http://localhost:5173
```

## Available Scripts

```bash
npm run dev
```

Starts the local development server.

```bash
npm run typecheck
```

Generates React Router types and runs TypeScript checks.

```bash
npm run build
```

Creates a production build.

```bash
npm run start
```

Runs the production build locally.

## Environment Variables

Only commit `.env.example`.

Do not commit `.env`, production secrets, backend credentials, database files,
or local machine-specific configuration.

Required frontend variable:

```env
VITE_API_URL=https://your-central-backend-url.com
```

For local development:

```env
VITE_API_URL=http://localhost:9000
```

## Vercel Deployment

You can deploy this frontend to Vercel even before the backend is deployed.
In that case, the UI and routes can be previewed, but API-based features such
as login, dashboard data, settings, and admin pages will only fully work after
the Central Backend is deployed and configured.

Basic Vercel setup:

1. Push this frontend repository to GitHub.
2. Open Vercel and import the repository.
3. Use:

```txt
Install Command: npm install
Build Command: npm run build
```

4. Add the environment variable:

```env
VITE_API_URL=https://your-central-backend-url.com
```

5. Deploy.

After the Central Backend is deployed, update `VITE_API_URL` in Vercel and
redeploy.

## Important Deployment Notes

- A deployed frontend cannot use `http://localhost:9000` for real users.
- `localhost` in production means the visitor's own computer, not your laptop.
- The Central Backend must allow the Vercel domain in CORS.
- Keep backend `.env` files, passwords, virtual environments, and databases out
  of this frontend repository.

## Current Backend Dependency

The frontend expects the Central Backend to provide endpoints such as:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `PATCH /api/users/me`
- `PATCH /api/users/me/password`
- `DELETE /api/users/me`
- dashboard, sessions, analytics, library, settings, and admin-data endpoints

Some business/data endpoints may still be under backend development. For the
current deployment, only the Central Backend and CRUD Backend are required.
