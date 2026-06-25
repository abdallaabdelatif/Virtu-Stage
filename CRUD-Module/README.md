## Local setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

By default the service uses local SQLite:

```env
DATABASE_URL=sqlite+aiosqlite:///./app.db
INTERNAL_API_KEY=development-internal-key-change-me
```

## Railway deployment

Deploy this folder as the CRUD service:

```text
Root Directory: /CRUD-Module
Railway Config File: /CRUD-Module/railway.toml
```

Add a Railway PostgreSQL service and set these variables on the CRUD service:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
INTERNAL_API_KEY=<same-secret-used-by-central-backend>
```

The app creates its tables and runs its lightweight migrations on startup.

## One-time admin bootstrap

After deployment, run the bootstrap script once with these variables set:

```env
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_PASSWORD=<strong-password>
```

Then run:

```bash
python -m scripts.bootstrap_admin
```
