# Starts the SmartFarm backend (which also serves the frontend) on http://localhost:8000
Set-Location "$PSScriptRoot\backend"
if (-not (Test-Path ".venv")) {
  python -m venv .venv
  .\.venv\Scripts\python -m pip install -r requirements.txt
}
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
