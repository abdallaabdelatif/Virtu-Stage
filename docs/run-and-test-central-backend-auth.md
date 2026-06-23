# Run and test Central Backend + CRUD (Auth)

This guide shows how to run the `CRUD-Module` service and the `central-backend` service locally, then test `register` and `login` using the Central Backend only.

Prerequisites
- Python 3.11+ installed
- Windows PowerShell (commands below use PowerShell) or `curl.exe` available

1) Start the CRUD service (port 8000)

Open a PowerShell terminal and run:

```powershell
cd CRUD-Module
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Leave this terminal running.

2) Start the Central Backend (port 9000)

Open a second PowerShell terminal and run:

```powershell
cd central-backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# copy example env or set env vars as needed
Copy-Item .env.example .env -ErrorAction SilentlyContinue
uvicorn app.main:app --reload --port 9000
```

Leave this terminal running.

3) Test Register (Central Backend only)

Use PowerShell `Invoke-RestMethod` to POST a new user through the Central Backend (it forwards to CRUD):

```powershell
$body = @{
  username = "alice"
  email = "alice@example.com"
  password = "Strong123!"
  first_name = "Alice"
  last_name = "A"
  gender = "female"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:9000/api/auth/register" -ContentType "application/json" -Body $body
```

Expected: HTTP 201 JSON response containing `access_token`, `token_type`, and
the created `user`. Duplicate usernames or emails return `409`.

4) Test Login (Central Backend only)

Login via Central Backend to receive a JWT access token:

```powershell
$login = @{
  username_or_email = "alice"
  password = "Strong123!"
} | ConvertTo-Json

$result = Invoke-RestMethod -Method Post -Uri "http://localhost:9000/api/auth/login" -ContentType "application/json" -Body $login
$result
```

Expected: JSON containing `access_token`, `token_type`, and `user`.

```json
{ "access_token": "<JWT>", "token_type": "bearer", "user": { "username": "alice" } }
```

5) Test the authenticated user endpoint

```powershell
$headers = @{ Authorization = "Bearer $($result.access_token)" }
Invoke-RestMethod -Method Get -Uri "http://localhost:9000/api/auth/me" -Headers $headers
```

Expected: the complete authenticated user object.

6) Test through the frontend

From the dashboard root:

```powershell
npm run dev
```

Open `http://localhost:5173`. Register, sign out, sign in using either the
username or email, and refresh the page to verify session restoration.
