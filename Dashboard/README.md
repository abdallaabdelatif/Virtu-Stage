# VirtuStage Dashboard

VirtuStage is a React dashboard for an AI-assisted VR training platform. Users
complete public-speaking or job-interview sessions in VR, then use the dashboard
to review Voice and Motion analysis, upload presentation material, manage their
accounts, and track performance over time.

This repository contains the VirtuStage dashboard frontend. It communicates
with the separately deployed Central Backend and does not expose internal
backend services or credentials to the browser.

## Production Architecture

```text
React dashboard (Vercel)
  -> Central Backend (Railway)
       -> CRUD Module -> PostgreSQL
       -> Voice Analysis
       -> Motion Analysis
       -> Conversational Component
       -> Gotenberg
       -> Cloudflare R2
```

The browser communicates only with the Central Backend. Internal services use
Railway private networking and are not exposed directly to dashboard users.

Production dashboard:

```text
https://virtu-stage-dashboard.vercel.app
```

## Current Features

- JWT registration, login, password reset, and authenticated session recovery.
- User and admin dashboards with statistics and charts.
- VR session history with status polling and score summaries.
- Detailed complete and partial Voice/Motion analysis reports.
- Voice feedback explanations, strengths, improvements, and next-session plans.
- PDF and PPTX content upload with asynchronous conversion status.
- User profile, password, avatar, and account management.
- Admin user listing, filtering, activation, and deletion.
- Loading skeletons, empty states, retry states, and last-good-data caching.

## Session and Report Status

The frontend maps backend session states into readable UI labels:

```text
pending      -> Pending
in_progress  -> In Progress
processing   -> Processing Analysis
completed    -> Completed
failed       -> Failed
cancelled    -> Cancelled
```

Non-terminal sessions are polled every three seconds. Polling stops when the
session becomes completed, failed, or cancelled, and an 11-minute client safety
limit prevents a broken request chain from polling forever.

Voice and Motion finish independently. A report can therefore be:

- `complete`: both analysis results are available;
- `partial`: one result is available and the other failed or timed out;
- `failed`: neither required result is available;
- `processing`: at least one required result is still pending.

For the detailed report header, a terminal report state is authoritative. A
complete report displays `Completed`; a partial or failed report displays
`Failed`; otherwise the latest polled session status is displayed. This avoids
showing `Processing Analysis` forever when a stored session row is older than
the effective component timeout.

## Tech Stack

- React 19
- React Router 7
- TypeScript
- Vite
- Tailwind CSS
- Axios
- Recharts
- SweetAlert2
- Vitest and Testing Library
- ESLint and Prettier
- Allure Vitest integration

## Local Setup

Install dependencies:

```bash
npm install
```

Create the local environment file:

```bash
cp .env.example .env
```

The frontend only reads this public build-time variable:

```env
VITE_API_URL=http://localhost:9000
```

Start the development server:

```bash
npm run dev
```

Open `http://localhost:5173`.

Do not place database passwords, provider API keys, signing keys, or internal
service credentials in `VITE_*` variables. Vite exposes those values to the
browser bundle.

## Available Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Start the React Router development server |
| `npm run build` | Create the production build |
| `npm run start` | Serve the generated production build locally |
| `npm run format` | Format the codebase with Prettier |
| `npm run format:check` | Check formatting without modifying files |
| `npm run lint` | Run ESLint with zero warnings allowed |
| `npm run typecheck` | Generate route types and run TypeScript checks |
| `npm run test` | Run the Vitest suite once |
| `npm run test:watch` | Run Vitest in watch mode |
| `npm run verify` | Run formatting, lint, type-checking, tests, and build |

The current frontend suite contains 37 tests across hooks, components, routes,
services, mappers, authentication, validation, and error handling.

## Main Frontend Structure

```text
app/
  components/   reusable UI components
  config/       API endpoint configuration
  context/      authentication state
  hooks/        polling and transient-message behavior
  mappers/      backend DTO to frontend-model conversion
  routes/       page-level route components
  services/     typed API access
  test/         shared test setup
  types/        DTO and frontend model definitions
  utils/        Axios client, dates, validation, and helpers
```

## Vercel Deployment

The Vercel project tracks the GitHub `main` branch. Every push to `main`
automatically creates a production deployment.

Configure this environment variable in Vercel:

```env
VITE_API_URL=https://your-central-backend.up.railway.app
```

Then commit and push changes:

```bash
git add <changed-files>
git commit -m "Describe the frontend change"
git push origin main
```

Wait for the newest Vercel deployment to become `Ready`. Redeploying an older
deployment before pushing will rebuild the old commit and will not include
local changes.

The Central Backend must include the dashboard origin in `CORS_ORIGINS` and
`FRONTEND_URL`, without an unnecessary trailing slash.

## Backend API Contract

The frontend expects the Central Backend to provide:

- authentication and current-user endpoints under `/api/auth`;
- user dashboard and account endpoints;
- session list, status, detail, and report endpoints under `/api/sessions`;
- content-library upload, conversion, retry, download, and deletion endpoints;
- admin dashboard and user-management endpoints.

VR WebSockets, service callbacks, database access, R2 credentials, analysis
provider keys, and Gotenberg configuration remain backend responsibilities.

## Verification

Before deploying frontend changes, run:

```bash
npm run verify
```

At the latest verification point, all 37 frontend tests passed together with
Prettier and TypeScript checks. A deployed synthetic end-to-end session also
confirmed the full transition:

```text
in_progress -> processing -> completed
```

with both Voice and Motion results stored in the final report.

## Security Notes

- Commit `.env.example`, never a real `.env` file.
- Never expose JWT signing secrets, internal API keys, database credentials,
  Cloudflare R2 secrets, or AI-provider keys in frontend variables.
- Rotate any credential that has been pasted into chat, logs, screenshots, or
  committed history.
- Use Railway private service URLs for backend-to-backend communication.
