# Stock Research App - Deployment Guide

## Railway Deployment (Backend + Frontend)

### Option 1: Monorepo Deploy (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/stock-research.git
   git push -u origin main
   ```

2. **Connect to Railway**
   - Go to https://railway.app
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repo
   - Railway will use `railway.toml` to deploy the backend

3. **Set Environment Variables**
   In Railway dashboard → Variables:
   ```
   DATABASE_URL = sqlite:////data/stock_data.db
   USE_MOCK_DATA = true
   ALLOWED_ORIGINS = https://your-frontend-domain.com
   ```

4. **Add Volume for SQLite**
   Railway dashboard → Volumes → Add Volume:
   - Mount path: `/data`
   - Size: 1GB (plenty for SQLite)

5. **Get your backend URL**
   After deploy, Railway gives you a URL like:
   `https://stock-research-production.up.railway.app`

### Option 2: Separate Frontend (Vercel/Netlify)

If you want the frontend on Vercel for faster static hosting:

1. **Update frontend API URL**
   ```bash
   cd frontend
   echo "VITE_API_URL=https://your-railway-backend.up.railway.app" > .env.production
   ```

2. **Deploy frontend to Vercel**
   ```bash
   npm i -g vercel
   vercel
   ```

3. **Update Railway CORS**
   Add your Vercel domain to `ALLOWED_ORIGINS`

## Local Development

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

Open http://localhost:5173

## Switching to Real Data

1. Get free API key from https://www.alphavantage.co/support/#api-key
2. Set in Railway:
   ```
   USE_MOCK_DATA = false
   ALPHA_VANTAGE_API_KEY = your_key_here
   ```
3. Redeploy

## Troubleshooting

- **SQLite locked errors**: Make sure the volume is mounted at `/data`
- **CORS errors**: Check `ALLOWED_ORIGINS` includes your frontend domain
- **No data loading**: Check `USE_MOCK_DATA` setting
