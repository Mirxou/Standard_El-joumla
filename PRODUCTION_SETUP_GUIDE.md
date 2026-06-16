# 🚀 Production Setup Guide - دليل إعداد الإنتاج

> Language: العربية | English  
> Version: v5.3.0  
> Status: 🟢 Ready for Production Deployment

---

## 📋 Quick Start - ابدأ السريع

### Prerequisites
```bash
# Required: Python 3.12+, Docker (optional for server mode)
python --version
# Expected: Python 3.12.8 or higher
```

### Step 1: Environment Setup
```bash
# Clone/navigate to project
cd "Logical Version trae"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production security libraries (optional but recommended)
pip install sqlcipher pycryptodome keyring cryptography
```

### Step 2: Configure Production Environment
```bash
# Copy example to production config
cp .env.example .env.production

# Edit with your production settings:
# - JWT_SECRET_KEY: Use a strong random key
# - DB credentials if using PostgreSQL
# - Email settings for alerts
```

### Step 3: Database Initialization
```bash
# Database migrations run automatically on first launch
# Or manually:
python -c "from src.core.database_manager import DatabaseManager; DatabaseManager('data/logical_release.db').initialize()"

# Verify database health
python verify_production.py
```

### Step 4: Run Application
```bash
# Desktop mode (local)
python main.py

# Server mode (API + optional web)
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔐 Security Configuration

### A. Database Encryption
```python
# Enable SQLCipher encryption (if installed)
# File: src/core/config_manager.py
USE_ENCRYPTION = True
CIPHER_ALGORITHM = "aes-256-cbc"
```

### B. Secret Management
```bash
# Set strong JWT secret
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Store in .env.production
JWT_SECRET_KEY=$JWT_SECRET_KEY
```

### C. API Authentication
```python
# All API endpoints require JWT token
Authorization: Bearer <token>

# Token obtained from login endpoint:
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "secure_password"
}
```

### D. 2FA/MFA Setup
```python
# Enable MFA for admin users
from src.services.mfa_service import MFAService

mfa = MFAService(db)
secret = mfa.generate_secret()  # Share with user
# User scans QR code in authenticator app
```

---

## 📊 Database Configuration

### SQLite (Default - Local/Desktop)
```python
# Automatic, stored at:
data/logical_release.db

# Backup before deployment:
cp data/logical_release.db data/logical_release.db.backup
```

### PostgreSQL (Server Mode)
```bash
# Update .env.production
DB_TYPE=postgres
DATABASE_URL=postgresql://user:password@localhost:5432/logical_release

# Docker compose automatically creates and connects
docker-compose -f docker-compose.prod.yml up postgres
```

### Backup Strategy
```bash
# Automated daily backup
data/backups/logical_release.db.2026-05-11.backup

# Manual backup
python scripts/backup_database.py

# Restore from backup
python scripts/restore_database.py backup_file.db
```

---

## 🐳 Docker Deployment (Server Mode)

### Build & Deploy
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### Services Started
- **API**: FastAPI at `http://localhost:8000`
- **PostgreSQL**: Database container
- **Redis**: Caching/background tasks (optional)
- **Web**: Next.js frontend at `http://localhost:3000` (optional)

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/api/v1/health

# Web frontend (if running)
curl http://localhost:3000
```

---

## 🧪 Pre-Launch Verification

### Run Tests
```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Verification Script
```bash
# Run production verification
python verify_production.py

# Expected output:
# ✅ Database initialized
# ✅ Inventory system working
# ✅ Sales system working
# ✅ MFA service available
# === System ready for production 100% ===
```

### Manual Smoke Test
```bash
# Desktop app smoke test
python test_ui_startup.py

# Expected: Main window opens, no errors
```

---

## 📈 Monitoring & Logs

### Log Files
```
logs/
├── __main__.log              # Desktop app logs
├── api.log                   # API server logs (if server mode)
├── database.log              # Database operations
├── window_telemetry.json     # Performance metrics
└── crash_reports/            # Error dumps
```

### Monitor Logs in Real-time
```bash
# Windows PowerShell
Get-Content .\logs\__main__.log -Wait

# Linux/Mac
tail -f logs/__main__.log
```

### Performance Monitoring
```bash
# Check system resources
# Windows:
Get-Process python | Select-Object WorkingSet64

# Linux/Mac:
ps aux | grep python
```

---

## 🚨 Troubleshooting

### Issue: Database locked
```bash
# Solution:
rm data/logical_release.db-wal data/logical_release.db-shm

# Restart application
```

### Issue: Port already in use (8000)
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or use different port in .env:
API_PORT=8001
```

### Issue: Import errors
```bash
# Verify Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: SQLCipher not available
```bash
# Still functional but without encryption
# To enable: pip install sqlcipher

# Check installation
python -c "import sqlcipher; print('SQLCipher ready')"
```

---

## 🔄 Rollback & Recovery

### Quick Rollback
```bash
# Stop current version
docker-compose -f docker-compose.prod.yml down

# Restore database backup
python scripts/restore_database.py data/backups/logical_release.db.backup

# Start previous version (if available)
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Restore
```bash
# Stop application
# Copy backup to active location:
cp data/logical_release.db.backup data/logical_release.db

# Restart
python main.py
```

---

## 📊 Performance Tuning

### Database Optimization
```python
# In src/core/database_manager.py
# Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

# Set cache size
PRAGMA cache_size = 10000;

# Enable query optimization
PRAGMA optimize;
```

### API Performance
```python
# Connection pooling in FastAPI
pool_size = 10
max_overflow = 20
```

### Caching Configuration
```python
# Redis cache (optional)
CACHE_USE_REDIS=1
REDIS_URL=redis://localhost:6379/0
```

---

## 🎯 Deployment Checklist

Before going live:
- [ ] All tests passing
- [ ] Security libraries installed
- [ ] JWT secret configured
- [ ] Database backed up
- [ ] Logs being captured
- [ ] Monitoring setup
- [ ] Rollback plan documented
- [ ] Team trained on operations

---

## 📞 Support & Escalation

### Error Reporting
1. Check logs: `logs/__main__.log`
2. Run verification: `python verify_production.py`
3. Review DEPLOYMENT_GUIDE.md
4. Contact development team with logs

### Critical Issues
- Database corruption: Restore from backup
- API down: Check Docker containers/processes
- Performance: Check logs for slowness, memory leaks

---

## 📚 Documentation References

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Detailed deployment procedures
- [Testing Guide](TESTING_GUIDE.md) - Test execution and CI/CD
- [Security Guide](docs/SECURITY_GUIDE.md) - Security configuration
- [API Documentation](docs/API_DOCUMENTATION.md) - API endpoints
- [README](README.md) - Project overview

---

**Version**: v5.3.0  
**Last Updated**: 2026-05-11  
**Status**: 🟢 Production Ready  
**Prepared By**: GitHub Copilot
