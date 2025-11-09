#!/bin/bash
# Script to update VPS with latest code changes from GitHub
# This script rebuilds the Docker image and restarts containers

set -e  # Exit on any error

echo "========================================="
echo "Updating VPS with latest code changes"
echo "========================================="

# Navigate to project directory
cd ~/projects/ecommerce || cd ~/ecommerce || exit 1

# Pull latest changes from GitHub
echo "1. Pulling latest changes from GitHub..."
git pull origin main || git pull origin master

# Stop containers
echo "2. Stopping containers..."
sudo docker compose down

# Rebuild Docker image (this includes your code changes)
echo "3. Rebuilding Docker image with latest code..."
sudo docker compose build --no-cache

# Start containers
echo "4. Starting containers..."
sudo docker compose up -d

# Wait for services to be ready
echo "5. Waiting for services to start..."
sleep 10

# Check service status
echo "6. Checking service status..."
sudo docker compose ps

echo ""
echo "========================================="
echo "Update complete!"
echo "========================================="
echo ""
echo "Your application has been updated with the latest code."
echo ""
echo "To view logs, run:"
echo "  docker compose logs -f"
echo ""
echo "To check if changes are applied, visit your website."
echo ""

