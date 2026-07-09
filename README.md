# Kalshi Legal & Regulatory Tracker

A web-based dashboard for monitoring Kalshi's legal battles, regulatory status, and transaction activity across US states.

## Features

- 📋 **Legal Cases Tracker** — Filter and view all ongoing legal challenges by jurisdiction and status
- 🗺️ **State Status Grid** — See operating approval status for each state with transaction metrics
- 📊 **Live Dashboard** — Real-time stats on total cases, approved states, active litigation, and monthly transaction volume
- 💰 **Transaction Analytics** — Monthly trading volume, active users, and contract types by state
- 🎯 **Interactive UI** — Responsive design with tab navigation and hover details

## Local Development

### Setup
```bash
pip install -r requirements.txt
python3 seed_data.py
python3 app.py
```

Visit `http://localhost:8001`

### Project Structure
```
.
├── app.py              # Flask REST API + static file server
├── index.html          # React-like SPA dashboard
├── seed_data.py        # Sample data initialization
├── requirements.txt    # Python dependencies
├── Procfile            # Heroku/Railway deployment config
└── kalshi.db          # SQLite database
```

## Deployment

### Backend (Flask API)

**Option A: Railway** (recommended - easiest)
1. Push to GitHub
2. Connect repo to Railway.app
3. Add `requirements.txt` and `Procfile`
4. Deploy — get live API URL

**Option B: Heroku**
```bash
heroku create kalshi-tracker
git push heroku main
heroku open
```

### Frontend (Static Site)

**Option A: Vercel** (recommended - fastest)
1. Push to GitHub
2. Import repo into Vercel
3. Set build command: `(none)` 
4. Set publish dir: `.`
5. Deploy — get live dashboard URL
6. Update `API_URL` in `index.html` to production backend

**Option B: GitHub Pages**
1. Push to GitHub
2. Enable Pages in settings
3. Visit `https://username.github.io/kalshi-tracker`

## API Endpoints

### Data
- `GET /api/stats` — Dashboard statistics
- `GET /api/cases` — All legal cases (filter: `jurisdiction`, `status`)
- `GET /api/states` — All state operating status
- `GET /api/transactions` — Transaction volume by state

### Mutations
- `POST /api/cases` — Add new case
- `POST /api/states` — Add/update state
- `POST /api/transactions` — Add transaction data

## Data Sources (Planned)

- **PACER** — Federal court cases (free API)
- **State AGs** — Regulatory filings and approvals
- **SEC EDGAR** — Company filings
- **News APIs** — Recent updates and developments
- **Manual updates** — Regulatory decisions and milestones

## Roadmap

- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Add PACER integration
- [ ] State regulatory data scraper
- [ ] Risk scoring system
- [ ] Case timeline visualization
- [ ] Export reports (CSV/PDF)
- [ ] Notification alerts for status changes
