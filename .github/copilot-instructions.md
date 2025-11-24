# Copilot Instructions for Standard_El-joumla

## Project Overview
- **Standard_El-joumla** is a professional ERP and trade management system with a desktop UI (PySide6/Qt), REST API (FastAPI), and advanced security (Argon2id, 2FA, encrypted backup).
- The architecture is modular: core logic (`src/core/`), business services (`src/services/`), data models (`src/models/`), and UI (`src/ui/`).
- Data flows from UI/API → validation (Pydantic) → business logic (services) → database (SQLite, connection pool, caching).

## Key Developer Workflows
- **Run all tests:** `python -m pytest -q` or `pytest -q`
- **Run a specific test:** `python -m pytest test_ai_features.py::TestVendorPortal::test_get_dashboard_empty -v`
- **Build & run desktop app:** `python main.py`
- **Run API server:** `python scripts/run_api_server.py` (serves docs at `/docs`)
- **Docker deploy:** `deploy.bat` (Windows) or `deploy.sh` (Linux/Mac)
- **Manual Docker:** `docker-compose up -d` (see `.env.example`)

## Project-Specific Patterns & Conventions
- **Security:** All passwords use Argon2id; 2FA (TOTP) is enforced for admin; brute-force protection is active (see `security_service.py`).
- **RBAC:** Role/permission checks are dynamic; RBAC schema adapts to column changes without destructive migrations.
- **Caching:** LRU+TTL cache for hot data (products, customers, reports); Redis optional via env vars.
- **Backup:** Encrypted backups (AES-256-GCM) with key in `config/backup_encryption.key`; always export key for disaster recovery.
- **API:** JWT required for all endpoints; see `API_IMPLEMENTATION_SUMMARY.md` for schemas and `openapi.json` for full spec.
- **Testing:** New features require tests in `tests/`; see `tests/test_slow_query_logging.py`, `tests/test_metrics_export.py` for examples.
- **Localization:** Full Arabic (RTL) and English support in UI and API.

## Integration & External Dependencies
- **PySide6** for UI, **FastAPI** for REST, **SQLite** (WAL mode) for DB, **Argon2-cffi** for password hashing, **PyOTP** for 2FA, **Cryptography** for backup.
- **Redis** (optional) for distributed cache; configure via `CACHE_USE_REDIS=1` and `REDIS_URL`.
- **Docker**: All services can be containerized; see `DOCKER_DEPLOYMENT.md` for cloud deployment.

## Examples & References
- **Accounting usage:** `examples_accounting_usage.py`
- **API usage:** `api_samples.http`, `API_DOCS.md`, `API_REFERENCE.md`
- **Backup/restore:** `backup_encrypted.py`, `check_db_tables.py`
- **Config:** `config/app_config.json`, `.env.example`
- **Release/test reports:** `COMPLETION_*.md`, `FINAL_ACHIEVEMENT_*.md`

## Special Notes
- Always check `README.md` for up-to-date workflows and new features.
- For new modules, follow the structure in `src/services/` and use Pydantic for validation.
- When in doubt, review `API_IMPLEMENTATION_SUMMARY.md` and `DATABASE_SCHEMA_INFO.md` for data flows and schema details.
