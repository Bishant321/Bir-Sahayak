"""Reproducible teaching fixture, not a simulation validated against real banking."""
import csv
from datetime import date, timedelta
from pathlib import Path
import random

from studentbank.settings import CATEGORIES, ROOT

MERCHANTS = {
    "groceries": ["Tesco", "Sainsburys", "Lidl", "Aldi", "Morrisons", "Asda", "Coop", "Waitrose", "Iceland", "Local Pantry"],
    "transport": ["TfL", "First Bus", "Stagecoach", "National Express", "Northern Rail", "Great Western", "Tramlink", "City Cabs", "Metro Travel", "Campus Shuttle"],
    "shopping": ["Primark", "H and M", "Uniqlo", "Argos", "Boots", "Waterstones", "Next", "TK Maxx", "Sports Direct", "Campus Store"],
    "bills": ["Octopus", "British Gas", "EDF", "Eon", "Thames Water", "Severn Trent", "Vodafone", "O2", "Sky", "Virgin Media"],
    "entertainment": ["Odeon", "Vue", "Cineworld", "Spotify", "Netflix", "Disney Plus", "Steam", "Xbox", "Ticketmaster", "Campus Cinema"],
}
PHRASES = {
    "groceries": ["weekly groceries", "food shop", "fresh fruit and veg", "bread milk and eggs", "supermarket groceries", "food essentials", "weekly food basket", "groceries top up"],
    "transport": ["bus ticket", "train fare", "travel pass", "transport journey", "commute fare", "return travel ticket", "student bus pass", "rail travel"],
    "shopping": ["clothes purchase", "shopping order", "student supplies", "retail purchase", "new shoes", "books and stationery", "online shopping", "clothing order"],
    "bills": ["monthly bill", "utility payment", "direct debit bill", "household utilities", "monthly service bill", "energy or broadband bill", "utilities direct debit", "household bill payment"],
    "entertainment": ["cinema tickets", "streaming subscription", "games purchase", "entertainment booking", "movie night", "music subscription", "leisure tickets", "entertainment subscription"],
}
RANGES = {"groceries": (200, 8000), "transport": (180, 6000), "shopping": (300, 15000),
          "bills": (800, 18000), "entertainment": (400, 6500)}


def generate(destination=None, seed=42):
    rng = random.Random(seed)
    rows = []
    for category in CATEGORIES:
        for merchant_index, merchant in enumerate(MERCHANTS[category]):
            for phrase in PHRASES[category]:
                pence = rng.randint(*RANGES[category])
                rows.append({"transaction_id": f"SB{len(rows)+1:05d}",
                             "date": (date(2026, 9, 1) + timedelta(days=rng.randrange(61))).isoformat(),
                             "description": f"{merchant} {phrase}",
                             "amount_gbp": f"{pence//100}.{pence%100:02d}", "currency": "GBP",
                             "category": category, "merchant_group": f"{category}_{merchant_index:02d}"})
    rng.shuffle(rows)
    destination = Path(destination or ROOT / "data/sample_transactions.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return destination
