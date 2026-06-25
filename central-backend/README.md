## Local setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```

## Railway deployment

Deploy this folder as the central backend service:

```text
Root Directory: /central-backend
Railway Config File: /central-backend/railway.toml
```

Required service variables:

```env
CRUD_BASE_URL=https://<crud-service-domain>.up.railway.app
INTERNAL_API_KEY=<same-secret-used-by-crud-service>
SECRET_KEY=<long-random-secret>
FRONTEND_URL=https://virtu-stage-dashboard.vercel.app
CORS_ORIGINS=https://virtu-stage-dashboard.vercel.app
ENVIRONMENT=production
```

This service does not connect directly to PostgreSQL and does not need `DATABASE_URL`.
The frontend should call this central backend URL, not the CRUD service URL.
