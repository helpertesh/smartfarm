"""Seeds reference data (market prices) on first start-up."""

from datetime import date, timedelta
import random

from app.data.market_seed import SEED_PRICES
from app.db.session import SessionLocal
from app.models.market import MarketPrice


def seed_market_prices() -> None:
    db = SessionLocal()
    try:
        if db.query(MarketPrice).count() > 0:
            return
        rng = random.Random(42)
        today = date.today()
        rows = []
        # 8 weekly data points per crop/market so price history charts have something to show.
        for crop_key, markets in SEED_PRICES.items():
            for market, base in markets.items():
                for weeks_ago in range(7, -1, -1):
                    drift = 1 + rng.uniform(-0.12, 0.12)
                    rows.append(
                        MarketPrice(
                            crop_key=crop_key,
                            market=market,
                            price_per_kg=round(base * (drift if weeks_ago else 1.0), 1),
                            currency="KES",
                            date=today - timedelta(weeks=weeks_ago),
                        )
                    )
        db.add_all(rows)
        db.commit()
    finally:
        db.close()
