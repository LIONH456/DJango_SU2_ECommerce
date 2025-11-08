# Docker Deployment Quick Start

This is a quick reference guide for deploying the Django ECommerce application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your VPS
- MongoDB Atlas connection string
- Environment variables configured in `.env` file

## Quick Start

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your actual values
   ```

2. **Run the startup script**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   Or manually:

3. **Build and start**:
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Run migrations** (first time only):
   ```bash
   docker compose run --rm web python manage.py migrate
   ```

5. **Create superuser** (optional):
   ```bash
   docker compose run --rm web python manage.py createsuperuser
   ```

## Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f web
docker compose logs -f nginx

# Restart services
docker compose restart

# Rebuild after code changes
docker compose build
docker compose up -d

# Run management commands
docker compose exec web python manage.py <command>

# Access container shell
docker compose exec web bash

# Check container status
docker compose ps
```

## File Structure

```
ECommerce/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Files to ignore in Docker build
├── .env.example            # Environment variables template
├── .env                    # Your actual environment variables (not in git)
├── nginx/
│   └── nginx.conf          # Nginx configuration
├── start.sh                # Startup script
└── DEPLOYMENT.md           # Full deployment guide
```

## Troubleshooting

See the main [DEPLOYMENT.md](DEPLOYMENT.md) file for detailed troubleshooting steps.

## For Complete Instructions

See [DEPLOYMENT.md](DEPLOYMENT.md) for the complete step-by-step deployment guide.

