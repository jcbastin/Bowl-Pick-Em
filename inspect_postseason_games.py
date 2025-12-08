import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CFBD_API_KEY")

YEAR = 2025  # we want to confirm postseason games for 2025

def inspect_games():
    url = f"https://api.collegefootballdata.com/games?year={YEAR}&seasonType=postseason"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    print(f"Fetching postseason games for {YEAR}...")
    resp = requests.get(url, headers=headers)

    print("Status Code:", resp.status_code)
    print()

    if resp.status_code != 200:
        print(resp.text)
        return

    games = resp.json()

    print(f"Total games returned: {len(games)}\n")

    for g in games:
        print(f"{g.get('away_team')} vs {g.get('home_team')} — {g.get('start_date')} — id={g.get('id')}")
    print()
    print("Done.")

if __name__ == "__main__":
    inspect_games()
