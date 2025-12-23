# Vercel Deployment Guide for FastAPI


## Prerequisites

1. **GitHub Account** - Sign up at https://github.com if you don't have one
2. **Vercel Account** - Sign up at https://vercel.com (use GitHub login for easy integration)
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

## Step 2: Deploy to Vercel

### Option A: Via Vercel Dashboard (Recommended for Beginners)

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Select **"Import Git Repository"**
4. Find and select your GitHub repository
5. Click **"Deploy"**
6. Wait for deployment to complete (~1-2 minutes)

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy (run from project root)
vercel
```

## Step 3: Test Your API

After deployment, Vercel will give you a URL like `https://your-project.vercel.app`

Test the API:

```bash
curl "https://your-project.vercel.app/api/recommend/user123?top_k=10"
```

Or open in browser:
```
https://your-project.vercel.app/api/recommend/user123?top_k=10
```

## Project Structure for Vercel

```
├── src/
│   ├── api/
│   │   └── main.py         # FastAPI app
│   └── constants.py        # Path constants
├── data/
│   └── processed/
│       └── synthetic_interactions.csv
├── vercel.json             # Vercel config
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
3. **Build fails**: Check Vercel build logs for errors

### Vercel Limits (Free Tier)

- 100GB bandwidth/month
- 10-second execution timeout
- 50MB max bundle size (including data files)

## Next Steps

- Add caching for better performance
- Add more recommendation endpoints
- Add authentication
- Connect to a database instead of CSV files
