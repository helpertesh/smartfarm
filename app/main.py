from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routers import auth, weather, crops, market, irrigation, analytics, farms

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgriHub API",
    description="Smart Agriculture Platform Backend",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(weather.router)
app.include_router(crops.router)
app.include_router(market.router)
app.include_router(irrigation.router)
app.include_router(analytics.router)
app.include_router(farms.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to AgriHub Smart Agriculture API 🌱"}