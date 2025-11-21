# Deployment Guide - Logical Version ERP

## 📋 Pre-Deployment Checklist

### 1. System Requirements
- ✅ Python 3.10+ installed
- ✅ 4GB RAM minimum (8GB recommended)
- ✅ 500MB disk space minimum
- ✅ Windows 10/11 or Linux (Ubuntu 20.04+)

### 2. Security Configuration

#### Change Default Admin Password
```bash
# First login with default credentials
Username: admin
Password: admin123

# Immediately change password via UI:
# Menu → Tools → Change Password
```

#### Enable 2FA (Mandatory for Production)
```bash
# Menu → Tools → Security Settings → Enable 2FA
# Scan QR code with Google Authenticator or Authy
# Save recovery codes in secure location
```

#### Update JWT Secret
```bash
# Edit .env file
JWT_SECRET_KEY=your-super-secret-random-key-here-min-32-chars

# Generate secure key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Database Setup

#### Initial Setup
```bash
# Database will be created automatically on first run
# Location: data/logical_release.db

# For production, ensure proper file permissions:
# Windows: Set folder permissions to restrict access
# Linux: chmod 600 data/logical_release.db
```

#### Backup Configuration
```bash
# Enable automatic backups
ENABLE_AUTO_BACKUP=True
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=data/backups

# Manual backup:
python scripts/backup_database.py
```

---

## 🚀 Deployment Steps

### Option 1: Desktop Application

#### Windows
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run application
python main.py

# 3. For startup shortcut, create .bat file:
@echo off
cd "C:\Path\To\Logical Version"
.venv\Scripts\activate
python main.py
```

#### Linux
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run application
python main.py

# 3. Create desktop entry (Ubuntu/Debian)
cat > ~/.local/share/applications/logical-version.desktop << EOF
[Desktop Entry]
Name=Logical Version
Exec=/path/to/venv/bin/python /path/to/main.py
Icon=/path/to/assets/icons/app-icon.png
Type=Application
Categories=Office;Finance;
EOF
```

### Option 2: API Server (Production)

#### Using Uvicorn (Development/Testing)
```bash
# Start server
python scripts/run_api_server.py

# Or directly:
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

#### Using Gunicorn (Production - Linux)
```bash
# 1. Install Gunicorn
pip install gunicorn

# 2. Start with multiple workers
gunicorn src.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --daemon
```

#### Using systemd (Linux Production)
```bash
# Create service file: /etc/systemd/system/logical-api.service
[Unit]
Description=Logical Version API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/logical-version
Environment="PATH=/opt/logical-version/.venv/bin"
ExecStart=/opt/logical-version/.venv/bin/gunicorn \
  src.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable logical-api
sudo systemctl start logical-api
sudo systemctl status logical-api
```

#### Using Windows Service
```powershell
# Using NSSM (Non-Sucking Service Manager)
# 1. Download NSSM from https://nssm.cc/download

# 2. Install service
nssm install LogicalAPI "C:\Path\To\.venv\Scripts\python.exe"
nssm set LogicalAPI AppDirectory "C:\Path\To\Logical Version"
nssm set LogicalAPI AppParameters "scripts\run_api_server.py"
nssm start LogicalAPI
```

---

## 🔒 Production Security Hardening

### 1. Firewall Configuration
```bash
# Linux (UFW)
sudo ufw allow 8000/tcp  # API port
sudo ufw enable

# Windows Firewall
# Use GUI or PowerShell:
New-NetFirewallRule -DisplayName "Logical API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### 2. Reverse Proxy (Nginx)
```nginx
# /etc/nginx/sites-available/logical-api
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/logical-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. SSL/TLS (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is configured automatically
```

### 4. Rate Limiting (Nginx)
```nginx
# Add to nginx config
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /auth/login {
        limit_req zone=api_limit burst=5;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Automated health check
python scripts/test_api_health.py

# Curl check
curl http://localhost:8000/health

# Expected response:
{"status":"ok","time":"2025-11-19T10:30:00Z"}
```

### Log Monitoring
```bash
# View logs
tail -f logs/app.log
tail -f logs/error.log
tail -f logs/access.log

# Log rotation (automatically configured)
# Logs rotate at 10MB, keep 5 backups
```

### Database Maintenance
```bash
# Vacuum database (monthly)
python scripts/optimize_database.py

# Verify integrity
sqlite3 data/logical_release.db "PRAGMA integrity_check;"

# Check size
du -h data/logical_release.db
```

### Backup Strategy
```bash
# Daily automated backups (configured in system)
# Verify backup
python scripts/verify_backup.py data/backups/latest.backup

# Offsite backup (recommended)
rsync -avz data/backups/ remote-server:/backups/logical-version/
```

---

## 🔄 Updates & Upgrades

### Updating Application
```bash
# 1. Backup current version
cp -r /opt/logical-version /opt/logical-version.backup

# 2. Pull updates
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Run migrations (if any)
python scripts/run_migrations.py

# 5. Restart service
sudo systemctl restart logical-api

# 6. Verify
python scripts/test_api_health.py
```

### Database Migrations
```bash
# Migrations are in: migrations/
# Run all pending migrations:
python scripts/run_migrations.py

# Check migration status:
python -c "from src.core.database_manager import DatabaseManager; db = DatabaseManager(); print(f'Tables: {db.get_table_count()}')"
```

---

## 🆘 Troubleshooting

### API Won't Start
```bash
# Check port availability
netstat -ano | findstr :8000  # Windows
ss -tulpn | grep :8000        # Linux

# Check logs
tail -50 logs/error.log

# Test imports
python -c "from src.api.app import app; print('OK')"
```

### Database Locked
```bash
# Close all connections
sudo systemctl stop logical-api

# Check for locks
fuser data/logical_release.db  # Linux

# Restart
sudo systemctl start logical-api
```

### JWT Token Issues
```bash
# Verify secret key is set
cat .env | grep JWT_SECRET_KEY

# Test token generation
python -c "from src.services.user_service import UserService; print('OK')"
```

### High Memory Usage
```bash
# Check worker count
# Reduce in gunicorn config:
--workers 2  # Instead of 4

# Enable connection pooling
# Already configured in DatabaseManager
```

---

## 📈 Performance Optimization

### Database Indexing
```sql
-- Already optimized via migrations
-- Check index usage:
SELECT name FROM sqlite_master WHERE type='index';
```

### Connection Pooling
```python
# Already configured in DatabaseManager
# Pool size: 10 connections
# Adjust in config/app_config.json if needed
```

### Caching
```python
# LRU cache with TTL already configured
# Adjust cache size in settings if needed
```

---

## 🔐 Compliance & Audit

### Audit Logs
```bash
# View security events
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100;

# Export audit trail
python scripts/export_audit_logs.py --start-date 2025-01-01
```

### User Activity
```bash
# Active sessions
SELECT username, last_activity FROM user_sessions WHERE active=1;

# Failed login attempts
SELECT * FROM login_attempts WHERE success=0 ORDER BY attempt_time DESC;
```

---

## 📞 Support & Resources

### Documentation
- **README.md** - Main documentation
- **API_IMPLEMENTATION_SUMMARY.md** - API technical docs
- **SECURITY_BACKUP_GUIDE.md** - Security best practices

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Logs Location
- Application: `logs/app.log`
- Security: `logs/security.log`
- Performance: `logs/performance.log`
- Errors: `logs/error.log`

---

## ✅ Post-Deployment Verification

Run all verification checks:

```bash
# 1. System tests
python scripts/run_system_tests.py

# 2. API health
python scripts/test_api_health.py

# 3. Security audit
python scripts/security_audit.py  # If available

# 4. Load test (optional)
# Use tools like Apache Bench or wrk
ab -n 1000 -c 10 http://localhost:8000/health
```

Expected results:
- ✅ All system tests pass (7/7)
- ✅ API health check passes
- ✅ Admin can login with 2FA
- ✅ All endpoints respond within 200ms
- ✅ Backups are being created

---

**Deployment completed successfully when all checks pass!** 🎉
