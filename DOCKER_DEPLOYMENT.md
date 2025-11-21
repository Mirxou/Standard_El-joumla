# 🐳 Docker Deployment Guide

## Quick Start

### 1. Prerequisites
```bash
# Install Docker & Docker Compose
# Windows: Download Docker Desktop
# Linux: 
sudo apt-get install docker.io docker-compose
```

### 2. Configuration
```bash
# Copy environment file
cp .env.example .env

# Edit .env and update:
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
# - SMTP settings for email OTP
# - SMS settings for SMS OTP (optional)
nano .env
```

### 3. Build & Run
```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Check status
docker-compose ps
```

### 4. Access Application
```
API: http://localhost:8000
API Docs: http://localhost:8000/docs
Health: http://localhost:8000/health
```

---

## Production Deployment

### AWS EC2

#### 1. Launch Instance
```bash
# Recommended: t3.medium or larger
# OS: Ubuntu 22.04 LTS
# Storage: 20GB minimum
# Security Group: Allow ports 80, 443, 8000
```

#### 2. Install Dependencies
```bash
# SSH into instance
ssh -i key.pem ubuntu@your-ec2-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 3. Deploy Application
```bash
# Clone repository
git clone https://your-repo.git
cd logical-version

# Configure environment
cp .env.example .env
nano .env  # Update production values

# Start services
docker-compose up -d

# Enable auto-start on reboot
sudo systemctl enable docker
```

#### 4. Setup SSL (Let's Encrypt)
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Update nginx.conf with SSL paths
# Restart nginx
docker-compose restart nginx
```

---

### Azure Container Instances

#### 1. Create Resource Group
```bash
az group create --name logical-version-rg --location eastus
```

#### 2. Create Container Registry (optional)
```bash
# Build and push image
az acr create --resource-group logical-version-rg --name logicalversionacr --sku Basic
az acr build --registry logicalversionacr --image logical-version:latest .
```

#### 3. Deploy Container
```bash
az container create \
  --resource-group logical-version-rg \
  --name logical-version-api \
  --image logicalversionacr.azurecr.io/logical-version:latest \
  --dns-name-label logical-version-api \
  --ports 8000 \
  --environment-variables \
    JWT_SECRET_KEY=your-secret \
    DATABASE_PATH=/app/data/logical_release.db \
  --azure-file-volume-account-name mystorageaccount \
  --azure-file-volume-account-key storage-key \
  --azure-file-volume-share-name logicalversiondata \
  --azure-file-volume-mount-path /app/data
```

---

### Google Cloud Run

#### 1. Build & Push to Container Registry
```bash
# Configure gcloud
gcloud auth login
gcloud config set project your-project-id

# Build image
gcloud builds submit --tag gcr.io/your-project-id/logical-version

# Deploy to Cloud Run
gcloud run deploy logical-version \
  --image gcr.io/your-project-id/logical-version \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "JWT_SECRET_KEY=your-secret,DATABASE_PATH=/app/data/logical_release.db"
```

---

## Scaling & High Availability

### Load Balancing (Multiple Instances)

```yaml
# docker-compose.yml
services:
  api:
    image: logical-version:latest
    deploy:
      replicas: 3  # Run 3 instances
      restart_policy:
        condition: on-failure
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Database Replication

```bash
# For production, use PostgreSQL instead of SQLite
# Update DATABASE_URL in .env:
DATABASE_URL=postgresql://user:pass@host:5432/logical_version

# Use managed database services:
# - AWS RDS
# - Azure Database for PostgreSQL
# - Google Cloud SQL
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Check resource usage
docker stats
```

### Backup Strategy
```bash
# Automatic backups are enabled by default
# Backups stored in: data/backups/

# Manual backup
docker-compose exec api python -c "from src.services.backup_service import BackupService; from src.core.database_manager import DatabaseManager; db = DatabaseManager(); bs = BackupService(db); bs.create_backup()"

# Download backup
docker cp logical-version-api:/app/data/backups ./local-backups
```

### Updates
```bash
# Pull latest changes
git pull

# Rebuild image
docker-compose build --no-cache

# Restart with zero downtime
docker-compose up -d --force-recreate

# Remove old images
docker image prune -a
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs api

# Check disk space
df -h

# Check permissions
ls -la data/
```

### Database locked
```bash
# Stop all containers
docker-compose down

# Remove lock files
rm data/*.db-wal data/*.db-shm

# Restart
docker-compose up -d
```

### API not responding
```bash
# Restart API service
docker-compose restart api

# Check health
curl http://localhost:8000/health

# Inspect container
docker-compose exec api bash
ps aux
```

---

## Security Checklist

- [ ] Change JWT_SECRET_KEY from default
- [ ] Enable MFA for all admin accounts
- [ ] Configure SSL/TLS certificates
- [ ] Enable firewall rules (allow only 80, 443)
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Enable rate limiting in nginx
- [ ] Use environment-specific .env files
- [ ] Regularly update dependencies
- [ ] Monitor security alerts

---

## Performance Tuning

### Application
```bash
# Increase API workers
API_WORKERS=8  # .env

# Enable caching
ENABLE_CACHE=true
CACHE_TTL=600
```

### Database
```bash
# Optimize SQLite
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;

# Or migrate to PostgreSQL for better concurrent access
```

### Nginx
```bash
# Enable gzip compression
gzip on;
gzip_types text/plain application/json;

# Increase worker connections
worker_connections 2048;
```

---

## Cost Optimization

### AWS
- Use t3.medium for <1000 users
- Use RDS instead of self-managed DB
- Enable auto-scaling
- Use CloudFront for static assets

### Azure
- Use B2s VM for small deployments
- Use Azure Database for PostgreSQL
- Enable auto-shutdown for dev/test

### Google Cloud
- Use Cloud Run (pay-per-use)
- Use Cloud SQL (managed database)
- Enable autoscaling based on CPU/memory

---

## Support

For issues or questions:
- GitHub: [Create Issue](https://github.com/your-repo/issues)
- Email: support@logical-version.com
- Docs: https://docs.logical-version.com
