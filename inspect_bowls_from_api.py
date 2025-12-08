import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer " + API_KEY}

r = requests.get(
    "https://api.collegefootballdata.com/games",
    headers=HEADERS,
    params={
        "year": 2025,
        "seasonType": "postseason",
        "division": "fbs"
    }
)

print("Status:", r.status_code)
games = r.json()

for g in games:
    print(g["id"], g.get("notes"), g.get("homeTeam"), g.get("awayTeam"))
