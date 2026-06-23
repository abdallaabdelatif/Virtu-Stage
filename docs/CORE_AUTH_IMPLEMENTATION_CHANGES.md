# Core Authentication Implementation Changes

## Files Changed

### CRUD service

Modified:

```text
backend/CRUD-Module/app/database.py
backend/CRUD-Module/app/main.py
backend/CRUD-Module/app/models/user.py
backend/CRUD-Module/app/routers/auth.py
backend/CRUD-Module/app/routers/user.py
backend/CRUD-Module/app/schemas/user.py
```

Added:

```text
backend/CRUD-Module/.env.example
backend/CRUD-Module/app/dependencies/__init__.py
backend/CRUD-Module/app/dependencies/internal.py
backend/CRUD-Module/app/migrations.py
backend/CRUD-Module/app/models/password_reset_token.py
backend/CRUD-Module/app/routers/password_reset.py
backend/CRUD-Module/app/schemas/auth.py
backend/CRUD-Module/app/security/__init__.py
backend/CRUD-Module/app/security/passwords.py
backend/CRUD-Module/scripts/__init__.py
backend/CRUD-Module/scripts/bootstrap_admin.py
```

### Central Backend

Modified:

```text
backend/central-backend/.env.example
backend/central-backend/app/api/protected.py
backend/central-backend/app/auth/deps.py
backend/central-backend/app/auth/passwords.py
backend/central-backend/app/auth/routes.py
backend/central-backend/app/auth/schemas.py
backend/central-backend/app/clients/crud_client.py
backend/central-backend/app/config.py
backend/central-backend/app/main.py
```

Added:

```text
backend/central-backend/app/api/account.py
backend/central-backend/app/api/admin.py
backend/central-backend/app/auth/authz.py
```

### Frontend

Modified:

```text
app/components/AdminRoute.tsx
app/components/ProtectedRoute.tsx
app/config/api.ts
app/mappers/userMapper.ts
app/routes/settings.tsx
app/services/adminService.ts
app/services/authService.ts
app/types/admin.dto.ts
app/types/auth.dto.ts
app/types/auth.ts
app/types/settings.ts
```

---

## Result

The five requested core authentication areas are now implemented:

1. Persisted user roles and account status.
2. Active-user and administrator authorization.
3. Forgot/reset password with hashed, expiring, single-use reset tokens.
4. Authenticated password change.
5. Authenticated account deletion with verified database cascades.

The architecture remains:

```text
Frontend :5173
    -> Central Backend :9000
        -> CRUD Service :8000
```

The frontend does not call CRUD directly.

## Database Changes

### User fields

Added to `users`:

```text
role: VARCHAR(20), default "user"
is_active: BOOLEAN, default true
```

Existing users were backfilled as:

```text
role = "user"
is_active = true
```

### Password reset tokens

Added `password_reset_tokens`:

```text
token_id
user_id
token_hash
expires_at
used_at
revoked_at
created_at
```

Only SHA-256 token hashes are stored. Plaintext reset tokens are not persisted.

### Migration strategy

The project did not contain Alembic. An idempotent migration runner was added in
`app/migrations.py`.

It:

- Creates a `schema_migrations` table.
- Detects the current `users` columns.
- Adds only missing `role` and `is_active` columns.
- Backfills existing rows.
- Records migration `20260623_core_auth`.
- Does not delete or recreate the existing database.

The migration was run successfully against the current SQLite database.

For a larger production deployment, adopting Alembic remains recommended.

### SQLite cascade enforcement

Every SQLite connection now executes:

```sql
PRAGMA foreign_keys=ON
```

Account-deletion testing confirmed cascades for:

- Training sessions
- Conversation histories
- Voice analysis
- Motion analysis
- Password reset tokens

## User Roles and Account Status

Public registration always creates:

```json
{
  "role": "user",
  "is_active": true
}
```

The registration schemas reject extra fields, so a client cannot submit its
own `role` or `is_active`.

Duplicate identity conflicts are separated:

```http
409 Conflict
```

Duplicate username:

```json
{
  "detail": "Username is already taken"
}
```

Duplicate email:

```json
{
  "detail": "An account with this email already exists"
}
```

The registration page displays each message underneath the responsible input,
adds a red border to that field, and clears the conflict when the user edits
the value. Unrelated network or server errors remain in the general error box.

Register, login, and `/api/auth/me` now return both fields.

Inactive accounts:

- Cannot log in.
- Cannot use `/api/auth/me`.
- Cannot use protected account endpoints.
- Receive `403 Forbidden`.

The current database user record is authoritative. Role and account status are
not trusted from JWT claims.

## Administrator Bootstrap

A one-time script was added:

```powershell
cd backend\CRUD-Module
.\venv\Scripts\activate
python -m scripts.bootstrap_admin
```

Required environment variables:

```env
BOOTSTRAP_ADMIN_USERNAME=
BOOTSTRAP_ADMIN_EMAIL=
BOOTSTRAP_ADMIN_PASSWORD=
```

The script:

- Requires a strong password.
- Does not use default credentials.
- Does not print the password.
- Does nothing when an administrator already exists.
- Can promote a matching existing user when no administrator exists.

## Internal Service Protection

New CRUD `/internal/...` endpoints require:

```http
X-Internal-API-Key: <shared key>
```

Both services read:

```env
INTERNAL_API_KEY=
```

The checked-in value is a development fallback and must be changed for
production.

## Final Browser-Facing Endpoints

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Create active regular user and return JWT |
| `POST` | `/api/auth/login` | Public | Verify credentials and active status |
| `GET` | `/api/auth/me` | Active user | Return current user |
| `POST` | `/api/auth/forgot-password` | Public | Create reset request without revealing account existence |
| `POST` | `/api/auth/reset-password` | Public reset token | Reset password once |
| `PATCH` | `/api/users/me/password` | Active user | Change password using current password |
| `PATCH` | `/api/users/me` | Active user | Update first and last name |
| `DELETE` | `/api/users/me` | Active user | Delete current account |
| `PATCH` | `/api/admin/users/{user_id}/status` | Admin | Enable or disable a regular account |

## Internal CRUD Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/internal/auth/login` | Verify credentials |
| `POST` | `/internal/users/by-email` | Private email lookup |
| `PATCH` | `/internal/auth/change-password` | Verify and atomically update password |
| `PATCH` | `/internal/users/{user_id}/status` | Persist account status |
| `PATCH` | `/internal/users/{user_id}/profile` | Persist first and last name |
| `POST` | `/internal/password-reset/request` | Revoke old tokens and store a new hash |
| `POST` | `/internal/password-reset/reset` | Atomically consume token and update password |

## Password Rules

The frontend, Central Backend, and CRUD enforce:

- At least eight characters.
- At least one uppercase letter.
- At least one lowercase letter.
- At least one number.
- At least one special character.

Passwords continue using the existing CRUD format:

```text
PBKDF2-HMAC-SHA256
100,000 iterations
32-byte random salt
base64(salt + digest)
```

## Forgot and Reset Password

Forgot-password always returns:

```json
{
  "message": "If an account exists for this email, a reset link has been sent."
}
```

It does not reveal whether the account exists or is active.

In development, the Central Backend logs:

```text
http://localhost:5173/reset-password?token=PLAINTEXT_TOKEN
```

The plaintext token is never returned by the API and is never stored.

Reset tokens are:

- Cryptographically random.
- Hashed before persistence.
- Valid for 15 minutes by default.
- Single-use.
- Revocable.
- Consumed using a conditional atomic database update.

Concurrent reset testing confirmed exactly one request succeeds and the other
receives `400`.

## Authenticated Change Password

Request:

```http
PATCH /api/users/me/password
Authorization: Bearer <access_token>
```

```json
{
  "current_password": "OldPassword@123",
  "new_password": "NewPassword@456"
}
```

The backend:

- Verifies the current password.
- Rejects weak passwords.
- Rejects reuse of the current password.
- Hashes the new password inside CRUD.

The Settings form is now controlled and functional. It shows loading and error
states, validates confirmation, and clears its fields after success.

## Profile Update

The frontend bio/professional-title field was removed because the current user
database schema does not persist it.

Profile updates now use:

```http
PATCH /api/users/me
Authorization: Bearer <access_token>
```

```json
{
  "first_name": "Alaa",
  "last_name": "Hassan"
}
```

The Central Backend derives the user ID from authentication and forwards the
validated names to the protected CRUD profile endpoint.

Settings now distinguishes toast styles:

- Successful changes use the green success icon.
- Backend and network failures use a red alert icon.

## Account Deletion

Request:

```http
DELETE /api/users/me
Authorization: Bearer <access_token>
```

The user ID comes only from the authenticated identity.

The frontend retains the SweetAlert2 confirmation, clears authentication after
success, and returns to login through the route guard.

CRUD account deletion now requires the internal service key.

## Administrator Account Status

Request:

```http
PATCH /api/admin/users/{user_id}/status
Authorization: Bearer <admin_access_token>
```

```json
{
  "is_active": false
}
```

Rules:

- Requires the current database role `admin`.
- Regular users receive `403`.
- An administrator cannot disable their own account.
- The administrator account cannot be disabled through the CRUD status
  operation.
- The frontend maps `disabled` to `!is_active`.

## Authorization and Ownership

Reusable dependencies now provide:

```text
get_current_user
get_current_active_user
require_admin
```

An ownership helper was added for future resource routes.

The Central Backend currently has no browser-facing session/file/report routes
to apply ownership checks to. Those future endpoints must:

1. Fetch the resource through CRUD.
2. Read its owner ID.
3. Compare it with the authenticated user ID.
4. Return `403` for an ownership failure.

## Verification Results

Passed:

- Existing SQLite schema migration.
- Existing-user role/status backfill.
- SQLite foreign-key enforcement.
- CRUD Python syntax/OpenAPI import.
- Central Backend Python syntax/OpenAPI import.
- Public registration defaults.
- Extra role/status registration rejection.
- Internal service-key rejection.
- Login and inactive-account rejection.
- Reset token storage and password reset.
- Reset-token reuse rejection.
- Concurrent reset-token use: one `200`, one `400`.
- Authenticated password change.
- Account status update.
- Account deletion cascade.
- Safe administrator bootstrap.
- Central Backend CORS preflight.
- Central auth/account/admin contract tests.
- Real Central Backend → CRUD network integration.
- Deleted account cannot log in.
- Frontend TypeScript type-check.
- Frontend production build.

Commands included:

```powershell
npm run typecheck
npm run build
```

Both passed.

## Running the Updated System

CRUD:

```powershell
cd backend\CRUD-Module
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Central Backend:

```powershell
cd backend\central-backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 9000
```

Frontend:

```powershell
npm run dev
```

## Manual Testing

### Register and login

1. Register a new account in the frontend.
2. Confirm the response contains `role=user` and `is_active=true`.
3. Sign out and log in using username or email.
4. Refresh and confirm `/api/auth/me` restores the user.

### Forgot/reset password

1. Submit the email on `/forgot-password`.
2. Read the development reset URL from the Central Backend terminal.
3. Open the URL.
4. Enter a strong new password.
5. Confirm the token cannot be reused.
6. Confirm the old password fails and the new password works.

### Change password

1. Log in.
2. Open Settings → Account.
3. Enter current, new, and confirmation passwords.
4. Confirm incorrect current passwords show an error.
5. Confirm success clears the fields.
6. Log in with the new password.

### Disable a user

1. Bootstrap the administrator.
2. Log in as administrator.
3. Send `PATCH /api/admin/users/{id}/status`.
4. Confirm the disabled user can no longer log in or call `/me`.

The full admin dashboard data endpoint is still not implemented, so the status
endpoint can currently be tested in Swagger or directly over HTTP.

### Delete account

1. Log in as a regular user.
2. Open Settings → Account.
3. Confirm account deletion.
4. Confirm the frontend returns to login.
5. Confirm the deleted credentials no longer work.

## Remaining Limitations

- Refresh tokens and server-side logout/revocation are not implemented.
- Reset emails are logged during development; no email provider is configured.
- The internal service key has a development fallback and must be replaced in
  production.
- The full admin dashboard endpoint is not implemented.
- Browser-facing session, file, report, and settings endpoints are not yet
  implemented in the Central Backend, so ownership enforcement for those
  resources remains future work.
- The migration runner is suitable for the current project and existing SQLite
  database; Alembic is still recommended before a larger production
  deployment.
- Access tokens remain in `localStorage`, with the previously documented XSS
  risk.
