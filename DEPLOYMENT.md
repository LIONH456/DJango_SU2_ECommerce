# 🚀 Deployment Guide for Render.com

## Prerequisites
- ✅ GitHub repository with your code
- ✅ Render.com account
- ✅ MongoDB Atlas account (for MongoDB in production)

## Step 1: Prepare Your Repository

### Files Created for Deployment:
- ✅ `requirements.txt` - Python dependencies
- ✅ `build.sh` - Build script for Render
- ✅ `render.yaml` - Render configuration
- ✅ `.gitignore` - Git ignore rules
- ✅ Updated `settings.py` - Production-ready settings

### Push to GitHub:
```bash
git add .
git commit -m "Prepare for Render.com deployment"
git push origin main
```

## Step 2: Set Up MongoDB Atlas (Cloud MongoDB)

1. **Go to [MongoDB Atlas](https://www.mongodb.com/atlas)**
2. **Create a free cluster**
3. **Get your connection string**
4. **Note down:**
   - Database name
   - Username
   - Password
   - Connection string

## Step 3: Deploy on Render.com

### Option A: Using render.yaml (Recommended)

1. **Go to [Render.com](https://render.com)**
2. **Click "New +" → "Blueprint"**
3. **Connect your GitHub repository**
4. **Render will automatically detect `render.yaml`**
5. **Click "Apply"**

### Option B: Manual Setup

1. **Go to [Render.com](https://render.com)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure:**
   - **Name**: `ecommerce-django`
   - **Environment**: `Python`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn ECommerce.wsgi:application`

## Step 4: Environment Variables

Add these environment variables in Render dashboard:

### Required Variables:
```
SECRET_KEY=your-secret-key-here
DEBUG=false
ALLOWED_HOSTS=.onrender.com
```

### Database Variables (from Render PostgreSQL):
```
DB_NAME=your-postgres-db-name
DB_USER=your-postgres-username
DB_PASSWORD=your-postgres-password
DB_HOST=your-postgres-host
DB_PORT=5432
```

### MongoDB Variables (from MongoDB Atlas):
```
MONGODB_HOST=your-mongodb-host
MONGODB_PORT=27017
MONGODB_DATABASE=your-database-name
MONGODB_COLLECTION=users
```

## Step 5: Database Setup

### PostgreSQL (Render will provide):
- Render automatically creates PostgreSQL database
- Use the connection details provided by Render

### MongoDB Atlas:
1. **Create a cluster**
2. **Get connection string**
3. **Add to environment variables**

## Step 6: Deploy and Test

1. **Click "Deploy"**
2. **Wait for build to complete**
3. **Check logs for any errors**
4. **Visit your app URL**

## Troubleshooting

### Common Issues:

1. **Build Fails:**
   - Check `requirements.txt` has all dependencies
   - Verify `build.sh` is executable

2. **Database Connection Error:**
   - Verify environment variables
   - Check database credentials

3. **Static Files Not Loading:**
   - Ensure `collectstatic` runs in build
   - Check `STATIC_ROOT` setting

4. **MongoDB Connection Error:**
   - Verify MongoDB Atlas connection string
   - Check network access settings

### Useful Commands:

```bash
# Test locally with production settings
python manage.py collectstatic --no-input
python manage.py migrate

# Check environment variables
python manage.py shell -c "from django.conf import settings; print(settings.DEBUG)"
```

## Post-Deployment

1. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

2. **Add sample data:**
   ```bash
   python manage.py create_sample_sliders
   ```

3. **Test all features:**
   - Homepage sliders
   - Admin dashboard
   - User authentication

## Monitoring

- **Check Render logs** for errors
- **Monitor database connections**
- **Test functionality regularly**

## Security Notes

- ✅ `DEBUG=false` in production
- ✅ `SECRET_KEY` is auto-generated
- ✅ HTTPS is enabled
- ✅ Security headers are configured

---

**Your app will be available at:** `https://your-app-name.onrender.com`
