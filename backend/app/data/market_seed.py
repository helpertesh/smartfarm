"""Seed market prices (KES per kg) for a few Kenyan markets.

These are indicative starting values maintained by the admin panel;
replace or extend them with real data from the admin API.
"""

MARKETS = [
    "Nairobi - Wakulima",
    "Nakuru - Wakulima",
    "Mombasa - Kongowea",
    "Kisumu - Jubilee",
    "Eldoret - Main",
]

# crop_key -> {market: price}
SEED_PRICES: dict[str, dict[str, float]] = {
    "tomato": {"Nairobi - Wakulima": 85, "Nakuru - Wakulima": 70, "Mombasa - Kongowea": 95, "Kisumu - Jubilee": 80, "Eldoret - Main": 75},
    "maize": {"Nairobi - Wakulima": 62, "Nakuru - Wakulima": 55, "Mombasa - Kongowea": 68, "Kisumu - Jubilee": 60, "Eldoret - Main": 50},
    "beans": {"Nairobi - Wakulima": 150, "Nakuru - Wakulima": 135, "Mombasa - Kongowea": 160, "Kisumu - Jubilee": 140, "Eldoret - Main": 130},
    "irish_potato": {"Nairobi - Wakulima": 70, "Nakuru - Wakulima": 55, "Mombasa - Kongowea": 85, "Kisumu - Jubilee": 75, "Eldoret - Main": 50},
    "onion": {"Nairobi - Wakulima": 120, "Nakuru - Wakulima": 110, "Mombasa - Kongowea": 130, "Kisumu - Jubilee": 115, "Eldoret - Main": 105},
    "kale": {"Nairobi - Wakulima": 40, "Nakuru - Wakulima": 30, "Mombasa - Kongowea": 50, "Kisumu - Jubilee": 35, "Eldoret - Main": 30},
    "cabbage": {"Nairobi - Wakulima": 35, "Nakuru - Wakulima": 25, "Mombasa - Kongowea": 45, "Kisumu - Jubilee": 30, "Eldoret - Main": 25},
    "sorghum": {"Nairobi - Wakulima": 55, "Nakuru - Wakulima": 50, "Mombasa - Kongowea": 60, "Kisumu - Jubilee": 48, "Eldoret - Main": 45},
    "sweet_potato": {"Nairobi - Wakulima": 45, "Nakuru - Wakulima": 40, "Mombasa - Kongowea": 55, "Kisumu - Jubilee": 38, "Eldoret - Main": 40},
    "cassava": {"Nairobi - Wakulima": 40, "Nakuru - Wakulima": 38, "Mombasa - Kongowea": 42, "Kisumu - Jubilee": 30, "Eldoret - Main": 36},
    "wheat": {"Nairobi - Wakulima": 58, "Nakuru - Wakulima": 52, "Mombasa - Kongowea": 62, "Kisumu - Jubilee": 56, "Eldoret - Main": 48},
    "banana": {"Nairobi - Wakulima": 60, "Nakuru - Wakulima": 50, "Mombasa - Kongowea": 55, "Kisumu - Jubilee": 45, "Eldoret - Main": 52},
}
