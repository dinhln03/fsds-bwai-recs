# Render Deployment Guide for FastAPI


## Prerequisites

1. **GitHub Account** - Sign up at https://github.com if you don't have one
2. **Render Account** - Sign up at https://render.com (use GitHub login for easy integration)
3. **Git installed** - Download from https://git-scm.com

## Step 1: Push Your Code to GitHub

```bash
# Initialize git (skip if already done)
git init

# Add all files
git add .

# Commit
git commit -m "Add recommendation API"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Render

### Option A: Via Render Dashboard (Recommended for Beginners)

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository
5. Configure the service:
   - **Name**: `bwai-recsys-api` (or your preferred name)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
6. Click **"Create Web Service"**
7. Wait for deployment to complete (~2-5 minutes)

### Option B: Via Blueprint (render.yaml)

The repository includes a `render.yaml` file for one-click deployment:

1. Go to https://dashboard.render.com/blueprints
2. Click **"New Blueprint Instance"**
3. Select your repository
4. Click **"Apply"**
5. Render will automatically configure and deploy your service

## Step 3: Test Your API

After deployment, Render will give you a URL like `https://bwai-recsys-api.onrender.com`

Test the API:

```bash
curl "https://bwai-recsys-api.onrender.com/recommend/user123?top_k=10"
```

Or open in browser:
```
https://bwai-recsys-api.onrender.com/recommend/user123?top_k=10
```

## Project Structure for Render

```
├── src/
│   ├── api/
│   │   └── main.py         # FastAPI app
│   └── constants.py        # Path constants
├── data/
│   └── processed/
│       └── synthetic_interactions.csv
├── render.yaml             # Render Blueprint config
└── requirements.txt        # Python dependencies
```

## Local Development

### Using uv (Recommended)

```bash
# Install dependencies
uv add fastapi pandas uvicorn

# Run locally
uv run uvicorn src.api.main:app --reload
```

### Test locally

```bash
curl "http://localhost:8000/recommend/user123?top_k=10"
```

## Troubleshooting


### Common Issues

1. **Import errors**: Make sure `requirements.txt` includes all dependencies
2. **File not found**: Check that data files are committed to git
3. **Build fails**: Check Render build logs for errors

### Render Limits (Free Tier)

- 750 hours/month of running time
- Services spin down after 15 minutes of inactivity
- First request after spin-down may take ~30 seconds (cold start)
- 512MB RAM
- 100GB bandwidth/month

## Next Steps

- Add caching for better performance
- Add more recommendation endpoints
- Add authentication
- Connect to a database instead of CSV files
- Upgrade to paid tier for always-on service
