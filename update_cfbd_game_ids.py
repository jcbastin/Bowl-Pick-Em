import os
import requests
import pandas as pd
from dotenv import load_dotenv

# --------------------------------------
# Load API Key
# --------------------------------------
load_dotenv()
API_KEY = os.getenv("CFBD_API_KEY")

YEAR = 2025

# IMPORTANT: Correct path to your actual CSV
CSV_PATH = "storage_seed/games.csv"


def fetch_postseason_games():
    """Fetch all postseason games from the CFBD API."""
    url = f"https://api.collegefootballdata.com/games?year={YEAR}&seasonType=postseason"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch postseason games: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()


def normalize_team_name(name: str) -> str:
    """Normalize team names between your CSV and CFBD naming."""
    if not name or "TBD" in name:
        return None
    return name.strip().replace("St.", "State")


def update_cfbd_ids():
    """Attach cfbd_game_id values to the games.csv file."""
    df = pd.read_csv(CSV_PATH)

    print("📥 Fetching postseason games from CFBD...")
    games = fetch_postseason_games()
    if games is None:
        return

    cfbd_lookup = []

    for g in games:
        cfbd_lookup.append({
            "cfbd_id": g.get("id"),
            "home_team": g.get("home_team"),
            "away_team": g.get("away_team"),
            "date": g.get("start_date"),
        })

    cfbd_df = pd.DataFrame(cfbd_lookup)

    print(f"🔍 Matching {len(df)} local games to {len(cfbd_df)} CFBD games...")

    matched = 0

    for idx, row in df.iterrows():
        away = normalize_team_name(row["away_team"])
        home = normalize_team_name(row["home_team"])

        if away is None or home is None:
            continue  # ignore CFP TBD matchups

        match = cfbd_df[
            (cfbd_df["away_team"] == away) &
            (cfbd_df["home_team"] == home)
        ]

        if len(match) == 1:
            df.at[idx, "cfbd_game_id"] = match.iloc[0]["cfbd_id"]
            matched += 1
        else:
            print(f"⚠️ No match for: {away} vs {home}")

    df.to_csv(CSV_PATH, index=False)

    print(f"✅ Updated cfbd_game_id for {matched} games.")
    print(f"📄 Saved updated file to {CSV_PATH}")


if __name__ == "__main__":
    update_cfbd_ids()
