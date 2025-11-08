#!/bin/bash
# Startup script for Django ECommerce Application
# This script helps with initial setup and running the application

set -e  # Exit on any error

echo "========================================="
echo "Django ECommerce - Startup Script"
echo "========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Create required directories
echo "Creating required directories..."
mkdir -p media staticfiles
chmod -R 755 media staticfiles

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed!"
    echo "Please install Docker first. See DEPLOYMENT.md for instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed!"
    echo "Please install Docker Compose first. See DEPLOYMENT.md for instructions."
    exit 1
fi

# Build Docker images
echo "Building Docker images..."
docker compose build

# Run migrations
echo "Running database migrations..."
docker compose run --rm web python manage.py migrate --no-input

# Collect static files
echo "Collecting static files..."
docker compose run --rm web python manage.py collectstatic --no-input

# Start services
echo "Starting services..."
docker compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 5

# Check service status
echo "Checking service status..."
docker compose ps

echo ""
echo "========================================="
echo "Application started successfully!"
echo "========================================="
echo ""
echo "Your application should be available at:"
echo "  http://YOUR_VPS_IP"
echo ""
echo "To view logs, run:"
echo "  docker compose logs -f"
echo ""
echo "To stop the application, run:"
echo "  docker compose down"
echo ""

