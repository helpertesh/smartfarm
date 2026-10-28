# 🌱 SmartFarm – Smart Agriculture Platform

A web platform that helps smallholder farmers make better decisions using weather data, rule-based crop advisory, an automatic crop calendar, disease information, irrigation guidance, market prices and farm analytics.

## Features

| Module | What it does |
|---|---|
| 🌦️ Weather intelligence | Live 7-day forecast (Open-Meteo, no API key) turned into farming recommendations: skip irrigation before rain, drainage before heavy rain, heat/cold/wind warnings, disease-risk warnings. |
| 🌾 Crop advisory | Rule engine scores 12 crops against soil type, season, water source, altitude, farm size and temperature. |
| 📅 Crop calendar | Pick a crop and planting date → full activity schedule (planting, weeding, top-dressing, pest scouting, harvest) with check-off and overdue tracking. |
| 🦠 Crop health | Select crop + symptoms → ranked possible diseases/pests with symptoms, conditions and recommended actions. Includes a browsable disease library. |
| 💧 Irrigation | Crop-stage water demand (crop coefficient × reference evapotranspiration) combined with recent and forecast rain and optional soil moisture. |
| 💰 Market prices | Latest prices per market, cross-market comparison and 90-day price trend. Admins maintain prices. |
| 📊 Farm analytics | Record income, expenses and harvests; revenue/expense/profit, monthly chart, expenses by category, harvest by crop with estimated value. |
| 📦 Farm inputs | Track seed, fertilizer, chemicals and feed in store; use/restock in one click; low-stock and out-of-stock alerts. |
| 🚨 Alerts | Weather, overdue/upcoming activities, harvest dates, disease-risk and low-stock alerts per farm. |
| 🛠️ Admin panel | Platform stats, user roles, market price updates. |

## Tech stack

- **Backend:** FastAPI, SQLAlchemy 2, Pydantic 2, JWT auth (python-jose), bcrypt
- **Database:** SQLite for local development, PostgreSQL in production (same code, change `DATABASE_URL`)
- **Frontend:** plain HTML, CSS and JavaScript (no build step), Chart.js for charts
- **External:** Open-Meteo forecast + geocoding APIs

## Project structure

```
backend/
  app/
    main.py            FastAPI app, CORS, static frontend serving
    core/              settings, JWT + password security
    db/session.py      engine, session, Base
    models/            User, Farm, CropPlan, FarmActivity, Transaction, Harvest, InputStock, MarketPrice
    schemas/           Pydantic request/response models
    routers/           auth, farms, weather, advisory, calendar, diseases, irrigation, market, analytics, inputs, alerts, admin
    services/          weather, advisory rules, calendar generator, irrigation, alerts
    data/              crop knowledge base, disease knowledge base, market seed prices
    seed.py            seeds market prices on first start
  requirements.txt
  .env.example
frontend/
  index.html           login / register
  dashboard.html       farmer dashboard
  farms.html, advisory.html, calendar.html, diseases.html, market.html, analytics.html, admin.html
  css/styles.css
  js/api.js            API client + helpers    js/layout.js  sidebar/auth guard    js/<page>.js
```

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # edit SECRET_KEY
uvicorn app.main:app --reload
```

Open http://localhost:8000 — the backend serves the frontend too. API docs are at http://localhost:8000/docs.

Or just run `.\run.ps1` (Windows) / `./run.sh` (macOS/Linux) from the project root.

The **first account you register becomes the admin**.

## Deploy

- **Backend → Render:** build `pip install -r backend/requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT` with root dir `backend`. Set `DATABASE_URL` to a PostgreSQL URL (`postgresql+psycopg://...`), a strong `SECRET_KEY`, and `CORS_ORIGINS` to your frontend URL.
- **Frontend → Vercel/Netlify:** deploy the `frontend/` folder as a static site and set `window.API_BASE` to the backend URL (e.g. add `<script>window.API_BASE="https://your-api.onrender.com"</script>` before `js/api.js` in each page, or inject it at build time).

## Roadmap

- [ ] SMS / push reminders for activities and alerts
- [ ] Image upload → AI disease detection
- [ ] IoT soil-moisture sensor integration for irrigation
- [ ] M-Pesa payments and connection to a Farm-to-Market marketplace
- [ ] Real market price feed instead of admin-maintained prices
