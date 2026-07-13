# Deployment Guide

Deploy Kalshi Legal Tracker to production in 10 minutes.

## Backend: Railway (Free Tier)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Authorize Railway to access your GitHub repos

### Step 2: Deploy Backend
1. Click **New Project**
2. Click **Deploy from GitHub repo**
3. Select `kalshi-tracker`
4. Railway auto-detects Python + Flask
5. Click **Deploy**
6. Wait for build to complete (~2 min)
7. Once deployed, copy your Railway URL (looks like `https://kalshi-tracker-prod.up.railway.app`)

### Step 3: Test Backend
```bash
curl https://YOUR-RAILWAY-URL/api/stats
```

You should get JSON with case stats. ✅

---

## Frontend: Vercel (Free Tier)

### Step 1: Update API URL
In `index.html`, find line ~496:

**Change:**
```javascript
const API_URL = 'http://localhost:8001/api';
```

**To:**
```javascript
const API_URL = 'https://YOUR-RAILWAY-URL/api';
```

**Example:**
```javascript
const API_URL = 'https://kalshi-tracker-prod.up.railway.app/api';
```

### Step 2: Commit and Push
```bash
git add index.html
git commit -m "Update API URL to production Railway URL"
git push
```

### Step 3: Deploy Frontend
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click **Add New...** → **Project**
4. Select `kalshi-tracker` repo
5. Settings should auto-configure (no build needed)
6. Click **Deploy**
7. Wait for deployment (~1 min)
8. Get your Vercel URL (looks like `https://kalshi-tracker.vercel.app`)

### Step 4: Test Frontend
Open https://YOUR-VERCEL-URL in your browser

You should see the full dashboard with:
- Real Kalshi litigation cases
- State operating status
- Transaction data
- US Map
- Automated scheduler running

---

## Post-Deployment

### Monitor Backend
- **Railway Dashboard** → View logs and status
- **API Health**: `https://YOUR-RAILWAY-URL/api/scheduler/status`

### Monitor Frontend
- **Vercel Dashboard** → View deployments
- **Analytics** → Track usage

### Scheduled Tasks (Running in Background)
- **Daily 2 AM**: SEC EDGAR filing check
- **Weekly Monday 9 AM**: Case status update

### Manual Updates
```bash
curl -X POST https://YOUR-RAILWAY-URL/api/scheduler/update-now \
  -H "Content-Type: application/json" \
  -d '{"action": "all"}'
```

---

## Environment Variables (Railway)

Add these in Railway Dashboard if needed:
- `FLASK_ENV=production`
- `DEBUG=false`
- `PORT=8000` (Railway auto-sets this)

---

## Troubleshooting

**"Cannot connect to API"**
- Verify Railway URL is correct
- Check CORS is enabled (it is in app.py)
- Wait 2-3 minutes after Railway deployment

**"API returns 500"**
- Check Railway logs: Railway Dashboard → Logs
- Verify database initialized (should auto-run)

**"Page shows blank"**
- Hard refresh browser (Cmd+Shift+R)
- Check browser console for errors (F12)
- Verify API URL in index.html

**"Scheduler not running"**
- Scheduler runs in Railway background
- Check logs for errors: Railway Dashboard → Logs
- Manually trigger: POST to `/api/scheduler/update-now`

---

## Cost

- **Railway free tier**: 500 hours/month (plenty for this app)
- **Vercel free tier**: unlimited static hosting
- **Total cost**: $0/month (unless you exceed free limits)

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Deploy frontend to Vercel
3. Share the Vercel URL with stakeholders
4. Monitor dashboards for usage
5. Expand data sources (add more states, real-time updates)
