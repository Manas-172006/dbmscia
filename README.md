# Found It

Found It is a campus portal for reporting found items, browsing available listings, and contacting the person who reported an item. Returned and archived records remain in MySQL but are excluded from public listings. The app does not support lost-item reports or automated matching.

The six milestone plan and product requirements are in [FOUND_IT_PRODUCT_SPEC.md](FOUND_IT_PRODUCT_SPEC.md).

## Requirements

- MySQL 8 (required; SQLite is not supported)
- Python 3.11+
- Node.js and npm

## Windows setup

### 1. Start MySQL 8

Open a PowerShell terminal. The local MySQL data directory and server script are under `backend`; start the server in its own terminal:

```powershell
cd C:\path\to\cia_dbms\backend
.\scripts\start-mysql.ps1
```

The script uses port `3307` by default and remains in the foreground. If you use an independently installed MySQL 8 service, configure its connection details instead.

Create the application database and accounts using a MySQL administrator account. Use unique passwords locally; never commit them:

```sql
CREATE DATABASE found_it_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'foundit_app'@'127.0.0.1' IDENTIFIED BY 'REPLACE_WITH_A_UNIQUE_APP_PASSWORD';
GRANT ALL PRIVILEGES ON found_it_db.* TO 'foundit_app'@'127.0.0.1';
CREATE USER 'foundit_explorer'@'127.0.0.1' IDENTIFIED BY 'REPLACE_WITH_A_DIFFERENT_UNIQUE_PASSWORD';
GRANT SELECT ON found_it_db.* TO 'foundit_explorer'@'127.0.0.1';
```

The SQL Explorer checks that its configured account has only `USAGE` and database-scoped `SELECT` grants. Do not grant it `INSERT`, `UPDATE`, `DELETE`, DDL, or global privileges.

### 2. Configure and initialize the backend

Open a second PowerShell terminal:

```powershell
cd C:\path\to\cia_dbms\backend
Copy-Item .env.example .env
```

Edit `backend\.env` locally. Set `DATABASE_URL` and `SQL_EXPLORER_DATABASE_URL` to the corresponding MySQL accounts, and replace the JWT and admin development values. The SQL Explorer URL must use the separate `foundit_explorer` account. `.env` is ignored by Git.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.db.seed
python -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive API documentation is at `/docs`.

### 3. Start the frontend

In another PowerShell terminal:

```powershell
cd C:\path\to\cia_dbms\frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal. The configured admin account can open the **Admin** link for live overview counts, safe table previews, relationships, and the predefined SQL Explorer.

## SQL Explorer safety

The Explorer accepts a predefined query ID and its declared integer parameters only. SQL text is stored in the backend catalogue, every query is validated as a single `SELECT`, and query values are passed as bound parameters. It rejects unknown parameters, out-of-range values, non-admin users, missing read-only configuration, and accounts with privileges beyond read-only access. It never accepts arbitrary SQL from the browser.

The Explorer uses `SQL_EXPLORER_DATABASE_URL`, a separate MySQL connection. Credentials, password hashes, JWT secrets, and environment values are not returned in the admin interface. The catalogue includes aggregation, joins, filters, subqueries, and MySQL views.

## Validation

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api.py tests\test_security.py
```

From `frontend`:

```powershell
npm run build
npm run lint
```

## Architecture

- `backend/app`: synchronous SQLAlchemy 2.x API and MySQL models
- `backend/alembic`: schema migrations, including the admin demonstration views
- `backend/app/queries/catalogue.py`: fixed SQL Explorer query catalogue
- `frontend/src`: React student portal and admin dashboard
- `backend/app/db/seed.py`: repeatable synthetic MySQL fixtures
