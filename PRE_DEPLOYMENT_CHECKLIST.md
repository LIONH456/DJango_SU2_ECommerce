# Pre-Deployment Checklist

Use this checklist to ensure everything is ready before deploying to your VPS.

## ✅ Files Created

- [x] `Dockerfile` - Docker image definition
- [x] `docker-compose.yml` - Docker Compose configuration
- [x] `.dockerignore` - Files to exclude from Docker build
- [x] `.env.example` - Environment variables template
- [x] `nginx/nginx.conf` - Nginx reverse proxy configuration
- [x] `DEPLOYMENT.md` - Complete deployment guide
- [x] `start.sh` - Startup script
- [x] `README_DOCKER.md` - Quick reference guide
- [x] `DEPLOYMENT_SUMMARY.md` - Files summary
- [x] `ECommerce/settings.py` - Updated for production

## 📋 Before Deployment

### 1. MongoDB Atlas Setup
- [ ] MongoDB Atlas account created
- [ ] Database cluster created
- [ ] Database user created with proper permissions
- [ ] Connection string obtained
- [ ] Network Access configured (add your VPS IP later)

### 2. Environment Variables
- [ ] Copy `.env.example` to `.env`
- [ ] Generate new `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your VPS IP
- [ ] Set `MONGODB_ATLAS_URI` with your connection string
- [ ] Configure email settings (Gmail App Password)
- [ ] Configure PayPal settings (if using)

### 3. VPS Preparation
- [ ] Ubuntu 24.02 VPS provisioned
- [ ] SSH access configured
- [ ] VPS IP address noted
- [ ] Root/sudo access available

### 4. Local Preparation
- [ ] All code changes committed
- [ ] Project files ready to transfer
- [ ] `.env` file ready (but NOT committed to git)

## 🚀 Deployment Steps

1. [ ] Connect to VPS via SSH
2. [ ] Update system packages
3. [ ] Install Docker (see DEPLOYMENT.md)
4. [ ] Install Docker Compose (see DEPLOYMENT.md)
5. [ ] Transfer project files to VPS
6. [ ] Copy `.env.example` to `.env` on VPS
7. [ ] Configure `.env` file on VPS
8. [ ] Run startup script or manual Docker commands
9. [ ] Configure firewall (UFW)
10. [ ] Test application in browser

## 🔒 Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] MongoDB Atlas network access configured
- [ ] Firewall (UFW) configured
- [ ] `.env` file has proper permissions (600)
- [ ] Non-root user created (optional but recommended)

## 📝 Important Notes

- **MongoDB Atlas**: You're using cloud MongoDB, so no local MongoDB container needed
- **Database**: Django still needs a database for sessions/admin (SQLite is fine)
- **Static Files**: Collected automatically on startup
- **Media Files**: Stored in `./media` directory (persistent)
- **Port**: Application runs on port 80 (HTTP)
- **SSL/HTTPS**: Can be added later when you have a domain

## 🆘 If Something Goes Wrong

1. Check logs: `docker compose logs -f`
2. Check container status: `docker compose ps`
3. Verify environment variables: `cat .env`
4. Review DEPLOYMENT.md troubleshooting section
5. Check MongoDB Atlas connection
6. Verify firewall settings

## 📚 Documentation

- **Complete Guide**: See `DEPLOYMENT.md`
- **Quick Reference**: See `README_DOCKER.md`
- **Files Summary**: See `DEPLOYMENT_SUMMARY.md`

## ✨ After Deployment

- [ ] Application accessible at `http://YOUR_VPS_IP`
- [ ] Admin panel accessible at `http://YOUR_VPS_IP/admin/`
- [ ] API endpoints working at `http://YOUR_VPS_IP/api/`
- [ ] Static files loading correctly
- [ ] Media uploads working
- [ ] MongoDB Atlas connection working
- [ ] Email sending working (test with order placement)

---

**Ready to deploy?** Follow the step-by-step instructions in `DEPLOYMENT.md`!

