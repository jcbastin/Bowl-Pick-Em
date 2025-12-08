import os
import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

load_dotenv()

API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

YEAR = 2025  # update if needed

GAMES_PATH = "storage_Seed/games.csv"   # path relative to backend folder
OUTPUT_PATH = "storage_Seed/games.csv"  # overwrite same file


# ---------------------------------------------------------------------
# FETCH TEAM RECORDS
# ---------------------------------------------------------------------

def fetch_team_records(year: int):
    url = f"https://api.collegefootballdata.com/records?year={year}"
    print(f"Fetching records for {year}...")

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise RuntimeError(f"CFBD error: {response.status_code}")

    data = response.json()

    # Build lookup: "Georgia" → "11-1"
    team_records = {}

    for team in data:
        wins = team.get("wins", 0)
        losses = team.get("losses", 0)
        team_name = team.get("team")

        if team_name:
            team_records[team_name] = f"{wins}-{losses}"

    print(f"Loaded {len(team_records)} team records.")
    return team_records


# ---------------------------------------------------------------------
# APPLY RECORDS TO GAMES.CSV
# ---------------------------------------------------------------------

def update_games_with_records():
    print("Loading games.csv...")
    df = pd.read_csv(GAMES_PATH)

    print("Fetching team records...")
    record_lookup = fetch_team_records(YEAR)

    # Create new columns if missing
    if "away_record" not in df.columns:
        df["away_record"] = ""
    if "home_record" not in df.columns:
        df["home_record"] = ""

    print("Applying records to each game...")
    for idx, row in df.iterrows():
        away = row["away_team"]
        home = row["home_team"]

        df.at[idx, "away_record"] = record_lookup.get(away, "")
        df.at[idx, "home_record"] = record_lookup.get(home, "")

    print("Saving updated CSV...")
    df.to_csv(OUTPUT_PATH, index=False)
    print("Done! Updated records saved to:", OUTPUT_PATH)


# ---------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------

if __name__ == "__main__":
    update_games_with_records()
