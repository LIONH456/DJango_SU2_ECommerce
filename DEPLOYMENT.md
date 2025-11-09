# Django ECommerce - VPS Deployment Guide

This guide provides step-by-step instructions for deploying your Django ECommerce application on an Ubuntu 24.02 VPS using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [VPS Initial Setup](#vps-initial-setup)
3. [Installing Docker](#installing-docker)
4. [Preparing Your Project](#preparing-your-project)
5. [Transferring Files to VPS](#transferring-files-to-vps)
6. [Configuring Environment Variables](#configuring-environment-variables)
7. [Building and Running with Docker](#building-and-running-with-docker)
8. [Setting Up Firewall](#setting-up-firewall)
9. [Post-Deployment](#post-deployment)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

---

## Prerequisites

Before starting, make sure you have:

- **Ubuntu 24.02 VPS** with root/sudo access
- **SSH access** to your VPS
- **MongoDB Atlas account** with connection string
- **Domain name (optional)** - we'll use IP address for now
- **Local machine** with Git installed (or SCP for file transfer)

---

## VPS Initial Setup

### Step 1: Connect to Your VPS

```bash
# On your local machine, connect to VPS via SSH
ssh root@YOUR_VPS_IP
# Or if using a different user:
ssh username@YOUR_VPS_IP
```

Replace `YOUR_VPS_IP` with your actual VPS IP address.

### Step 2: Update System Packages

```bash
# Update package list
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git ufw
```

### Step 3: Create a Non-Root User (Recommended)

```bash
# Create a new user
sudo adduser ecommerce

# Add user to sudo group
sudo usermod -aG sudo ecommerce

# Switch to the new user
su - ecommerce
```

---

## Installing Docker

### Step 1: Install Docker

```bash
# Remove old versions if any
sudo apt remove -y docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index
sudo apt update

# Install Docker Engine
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 2: Add User to Docker Group (Optional but Recommended)

```bash
# Add your user to docker group (so you don't need sudo for docker commands)
sudo usermod -aG docker $USER

# Apply the new group membership
newgrp docker

# Verify you can run docker without sudo
docker run hello-world
```

### Step 3: Start and Enable Docker

```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check Docker status
sudo systemctl status docker
```

---

## Preparing Your Project

### Step 1: Organize Project Structure

On your **local machine**, ensure your project has the following structure:

```
ECommerce/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── requirements.txt
├── manage.py
├── nginx/
│   └── nginx.conf
├── ECommerce/
│   └── settings.py
├── main/
├── dashboard/
├── templates/
├── static/
└── media/  (create if doesn't exist)
```

### Step 2: Create Required Directories

On your **local machine**:

```bash
# Create nginx directory if it doesn't exist
mkdir -p nginx

# Create media directory if it doesn't exist
mkdir -p media

# Create staticfiles directory (will be populated by collectstatic)
mkdir -p staticfiles
```

---

## Transferring Files to VPS

### Option 1: Using Git (Recommended)

```bash
# On your VPS, create a directory for the project
mkdir -p ~/projects
cd ~/projects

# Clone your repository (if it's on GitHub/GitLab)
git clone https://github.com/yourusername/your-repo.git ecommerce
cd ecommerce

# Or if using SSH
git clone git@github.com:yourusername/your-repo.git ecommerce
cd ecommerce
```

### Option 2: Using SCP (Secure Copy)

On your **local machine**:

```bash
# Copy the entire project directory to VPS
scp -r /path/to/your/ECommerce project root@YOUR_VPS_IP:/root/projects/ecommerce

# Or if using a different user
scp -r /path/to/your/ECommerce project ecommerce@YOUR_VPS_IP:/home/ecommerce/projects/ecommerce
```

### Option 3: Using rsync (Recommended for Updates)

On your **local machine**:

```bash
# Sync project files to VPS (excludes unnecessary files)
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
  /path/to/your/ECommerce/ root@YOUR_VPS_IP:/root/projects/ecommerce/
```

### Step: Verify Files on VPS

```bash
# On your VPS, navigate to project directory
cd ~/projects/ecommerce  # or wherever you placed it

# List files to verify
ls -la

# Check that required files exist
ls -la Dockerfile docker-compose.yml .env.example nginx/nginx.conf
```

---

## Configuring Environment Variables

### Step 1: Create .env File

```bash
# On your VPS, navigate to project directory
cd ~/projects/ecommerce

# Copy the example environment file
cp .env.example .env

# Edit the .env file
nano .env
```

### Step 2: Configure Environment Variables

Edit the `.env` file with your actual values:

```bash
# Django Settings
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
# For production with domain: yourdomain.com,www.yourdomain.com,YOUR_VPS_IP
# For IP only: YOUR_VPS_IP
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR_VPS_IP
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
USE_HTTPS=True

# MongoDB Atlas (your cloud database)
MONGODB_ATLAS_URI=mongodb+srv://username:password@cluster.mongodb.net/ECommerceSU2?retryWrites=true&w=majority

# Email Configuration (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# PayPal Configuration
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox  # Change to 'live' for production

# Telegram Bot Configuration (for owner notifications)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_CHAT_ID=your-telegram-chat-id-here
```

**Important Notes:**

1. **SECRET_KEY**: Generate a new secret key:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **ALLOWED_HOSTS**: Replace `YOUR_VPS_IP` with your actual VPS IP address (e.g., `123.45.67.89`)

3. **MONGODB_ATLAS_URI**: Get this from MongoDB Atlas Dashboard -> Connect -> Connect your application

4. **Gmail App Password**: 
   - Go to Google Account -> Security -> 2-Step Verification -> App passwords
   - Generate an app password for "Mail"
   - Use this password (not your regular Gmail password)

5. **Save and exit**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Set Proper Permissions

```bash
# Make sure .env file is readable only by you
chmod 600 .env
```

---

## Building and Running with Docker

### Step 1: Navigate to Project Directory

```bash
cd ~/projects/ecommerce
```

### Step 2: Create Required Directories

```bash
# Create directories for media and staticfiles
mkdir -p media staticfiles

# Set proper permissions
chmod -R 755 media staticfiles
```

### Step 3: Build Docker Images

```bash
# Build the Docker images
docker compose build

# This may take a few minutes the first time
```

### Step 4: Run Database Migrations

```bash
# Run migrations to set up the database
docker compose run --rm web python manage.py migrate

# Create a superuser (admin user) if needed
docker compose run --rm web python manage.py createsuperuser
```

### Step 5: Collect Static Files

```bash
# Collect static files (this is also done automatically in docker-compose.yml)
docker compose run --rm web python manage.py collectstatic --no-input
```

### Step 6: Start the Application

```bash
# Start all services in detached mode (runs in background)
docker compose up -d

# Check if containers are running
docker compose ps

# View logs
docker compose logs -f
```

### Step 7: Verify Application is Running

```bash
# Check if web service is running
curl http://localhost:8000

# Check if nginx is running
curl http://localhost

# View container logs
docker compose logs web
docker compose logs nginx
```

---

## Setting Up Firewall

### Step 1: Configure UFW (Uncomplicated Firewall)

```bash
# Allow SSH (important - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP (port 80)
sudo ufw allow 80/tcp

# Allow HTTPS (port 443) - for future SSL certificate
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check firewall status
sudo ufw status
```

### Step 2: Verify Firewall Rules

```bash
# List all rules
sudo ufw status verbose
```

---

## Post-Deployment

### Step 1: Test Your Application

1. **Open your browser** and navigate to `http://YOUR_VPS_IP`
2. **Verify the homepage loads** correctly
3. **Test admin panel** at `http://YOUR_VPS_IP/admin/`
4. **Test API endpoints** at `http://YOUR_VPS_IP/api/`

### Step 2: Create Admin User (if not done already)

```bash
# Create superuser
docker compose exec web python manage.py createsuperuser

# Follow the prompts to create an admin user
```

### Step 3: Configure MongoDB Atlas Network Access

1. **Go to MongoDB Atlas Dashboard**
2. **Navigate to Network Access**
3. **Add your VPS IP address** to the allowed list
4. **Save the changes**

### Step 4: Set Up Automatic Restart

Docker Compose is already configured to restart containers automatically. Verify:

```bash
# Check container restart policy
docker compose ps

# Containers should show "Restart: unless-stopped"
```

---

## Troubleshooting

### Issue: Containers won't start

```bash
# Check container logs
docker compose logs

# Check specific service logs
docker compose logs web
docker compose logs nginx

# Restart containers
docker compose restart
```

### Issue: Static files not loading

```bash
# Recollect static files
docker compose exec web python manage.py collectstatic --no-input

# Check static files directory
ls -la staticfiles/

# Restart web container
docker compose restart web
```

### Issue: Database connection errors

```bash
# Check MongoDB Atlas connection string in .env
cat .env | grep MONGODB_ATLAS_URI

# Verify MongoDB Atlas network access allows your VPS IP
# Test connection from VPS
docker compose exec web python -c "from pymongo import MongoClient; import os; client = MongoClient(os.getenv('MONGODB_ATLAS_URI')); print(client.server_info())"
```

### Issue: Permission denied errors

```bash
# Fix permissions for media and staticfiles
sudo chown -R $USER:$USER media staticfiles
chmod -R 755 media staticfiles

# Restart containers
docker compose restart
```

### Issue: Port already in use

```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80

# Or
sudo lsof -i :80

# Stop the conflicting service or change port in docker-compose.yml
```

### Issue: Can't access application from browser

```bash
# Check if containers are running
docker compose ps

# Check if firewall allows port 80
sudo ufw status

# Check nginx logs
docker compose logs nginx

# Test locally on VPS
curl http://localhost
```

### View Real-time Logs

```bash
# Follow all logs
docker compose logs -f

# Follow specific service logs
docker compose logs -f web
docker compose logs -f nginx
```

---

## Maintenance

### Updating the Application

```bash
# Navigate to project directory
cd ~/projects/ecommerce

# Pull latest changes (if using Git)
git pull

# Rebuild Docker images
docker compose build

# Run migrations
docker compose run --rm web python manage.py migrate

# Recollect static files
docker compose run --rm web python manage.py collectstatic --no-input

# Restart containers
docker compose restart
```

### Backup Important Data

```bash
# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Backup database (if using PostgreSQL)
# For MongoDB Atlas, use Atlas backup features

# Backup environment file
cp .env .env.backup
```

### Monitoring

```bash
# Check container status
docker compose ps

# Check resource usage
docker stats

# Check disk space
df -h

# Check application logs
docker compose logs --tail=100 web
```

### Stopping the Application

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (CAUTION: This deletes data!)
docker compose down -v
```

### Starting the Application

```bash
# Start all containers
docker compose up -d

# Start with logs visible
docker compose up
```

---

## Additional Configuration

### Setting Up Domain Name (Future)

When you get a domain name:

1. **Update .env file**:
   ```bash
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR_VPS_IP
   ```

2. **Update nginx.conf**:
   ```nginx
   server_name yourdomain.com www.yourdomain.com;
   ```

3. **Update DNS records** to point to your VPS IP

4. **Set up SSL certificate** (Let's Encrypt):
   ```bash
   # Install certbot
   sudo apt install certbot python3-certbot-nginx

   # Get SSL certificate
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

### Setting Up SSL/HTTPS (Future)

1. Install Certbot
2. Get SSL certificate
3. Update nginx configuration for HTTPS
4. Update Django settings for HTTPS

---

## Security Checklist

- [ ] Changed default SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configured ALLOWED_HOSTS with your IP
- [ ] Set up firewall (UFW)
- [ ] Used strong passwords for all services
- [ ] MongoDB Atlas network access configured
- [ ] .env file has proper permissions (600)
- [ ] Regular backups configured
- [ ] SSL certificate installed (when domain is available)

---

## Support

If you encounter any issues:

1. Check the logs: `docker compose logs`
2. Verify environment variables: `cat .env`
3. Check container status: `docker compose ps`
4. Review this guide's troubleshooting section

---

## Quick Reference Commands

```bash
# Start application
docker compose up -d

# Stop application
docker compose down

# View logs
docker compose logs -f

# Restart application
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

---

**Congratulations!** Your Django ECommerce application should now be running on your VPS. Visit `http://YOUR_VPS_IP` in your browser to see it in action!

