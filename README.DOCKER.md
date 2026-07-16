# 🐳 Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Setup

1. **Copy environment file:**
```bash
cp .docker.env.example .docker.env
```

2. **Edit `.docker.env` with your configuration:**
```bash
# Set secure passwords
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Check status:**
```bash
docker-compose ps
```

5. **View logs:**
```bash
docker-compose logs -f api
```

### Access Points

- **REST API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

### Development Mode

For development with hot-reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

### Stop Services

```bash
docker-compose down
```

### Clean Everything

```bash
docker-compose down -v  # Removes volumes
docker-compose build --no-cache  # Rebuilds images
```

## Architecture

```
┌─────────────┐
│   Web App   │ (React)
│  Port 3000  │
└──────┬──────┘
       │
┌──────▼──────┐
│  REST API   │ (FastAPI)
│  Port 8000  │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌──▼──┐
│Post │ │Redis│
│gres │ │     │
└─────┘ └─────┘
```

## Monitoring

### Prometheus Metrics

The API exposes metrics at `/api/v1/metrics` for Prometheus scraping.

### Grafana Dashboards

Pre-configured dashboards are available in `monitoring/grafana/dashboards/`.

## Troubleshooting

### Database Connection Issues

Check PostgreSQL logs:
```bash
docker-compose logs postgres
```

### API Not Starting

Check API logs:
```bash
docker-compose logs api
```

### Port Conflicts

If ports are already in use, modify `docker-compose.yml` to use different ports.

## Production Deployment

For production:

1. Use strong passwords in `.docker.env`
2. Enable SSL/TLS (use reverse proxy like Nginx)
3. Set up regular backups
4. Configure monitoring alerts
5. Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)

