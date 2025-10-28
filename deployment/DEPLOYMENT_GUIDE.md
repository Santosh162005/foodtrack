# Deployment Guide - Food Expiry Tracker

## ⚠️ IMPORTANT: InfinityFree Compatibility Issue

**This is a Python Flask application and CANNOT be deployed on InfinityFree** because InfinityFree only supports PHP hosting, not Python.

## Recommended Hosting Platforms for Python Flask Apps

### 1. **PythonAnywhere** (Recommended - Free Tier Available)
- Visit: https://www.pythonanywhere.com
- Free tier includes: Python support, MySQL database
- Steps:
  1. Create account
  2. Upload all files from this deployment folder
  3. Set up virtual environment
  4. Configure MySQL database
  5. Set web app configuration

### 2. **Render** (Free Tier)
- Visit: https://render.com
- Free tier with automatic deployments from Git
- Supports Python and PostgreSQL

### 3. **Railway** (Free Trial)
- Visit: https://railway.app
- Easy deployment with MySQL support

### 4. **Heroku** (Paid - Free tier discontinued)
- Visit: https://heroku.com
- Reliable but requires payment

## Files Included in This Deployment Package

```
deployment/
├── app.py              # Main Flask application (MySQL version)
├── app_sqlite.py       # SQLite version (for local testing)
├── ocr_model.py        # OCR functionality
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── database.sql        # MySQL database schema
├── recipes.json        # Recipe data
├── static/            # CSS, JS, and uploaded images
└── templates/         # HTML templates
```

## Quick Deployment Steps for PythonAnywhere

1. **Create Account**: Sign up at pythonanywhere.com

2. **Upload Files**: 
   - Use the Files tab to upload all files from this deployment folder
   - Or use Git to clone your repository

3. **Set Up Virtual Environment**:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 foodtracker
   pip install -r requirements.txt
   ```

4. **Configure Database**:
   - Go to Databases tab
   - Create MySQL database
   - Import database.sql
   - Update DB_CONFIG in app.py with your credentials

5. **Configure Web App**:
   - Go to Web tab
   - Add new web app
   - Choose Manual configuration
   - Select Python 3.10
   - Set source code directory
   - Edit WSGI file to point to your app

6. **Set Environment Variables**:
   - Create .env file from .env.example
   - Add your API keys and secrets

## Alternative: Use SQLite Version (Simpler)

For simpler deployment without MySQL:
- Rename `app_sqlite.py` to `app.py`
- Remove MySQL from requirements.txt
- Database will be created automatically

## Environment Variables Needed

Create a `.env` file with:
```
SECRET_KEY=your_secret_key_here
GEMINI_API_KEY=your_google_api_key
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Support

For deployment help:
- PythonAnywhere: https://help.pythonanywhere.com
- Render: https://render.com/docs
- Railway: https://docs.railway.app
