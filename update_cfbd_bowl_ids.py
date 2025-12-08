import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

CSV_PATH = "./storage_seed/games.csv"   # or ./storage/games.csv


def fetch_postseason_games(year=2025):
    url = f"https://api.collegefootballdata.com/games?year={year}&seasonType=postseason&division=fbs"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"CFBD Error {r.status_code}")
        return []
    return r.json()


def match_game(csv_row, api_games):
    """
    Matches by:
    1. Both home + away team (best)
    2. Bowl name + partial team match
    3. Bowl name only (if teams TBD)
    """

    csv_bowl = csv_row["bowl_name"].lower().replace("’", "'").replace("ʻ", "'")
    csv_home = str(csv_row["home_team"]).lower()
    csv_away = str(csv_row["away_team"]).lower()

    best_match = None

    for g in api_games:
        api_bowl = g.get("notes", "").lower() if g.get("notes") else ""
        api_home = (g.get("home_team") or "").lower()
        api_away = (g.get("away_team") or "").lower()

        # 1. Exact team-team match
        if csv_home == api_home and csv_away == api_away:
            return g

        # 2. Bowl name substring match (CFBD sometimes stores bowl name inside "notes")
        if csv_bowl and csv_bowl in api_bowl:
            best_match = g

        # 3. If teams are TBD but bowl name matches exactly (CFBD sets home/away to None)
        if "tbd" in csv_home and "tbd" in csv_away and csv_bowl in api_bowl:
            best_match = g

    return best_match


def update_csv():
    df = pd.read_csv(CSV_PATH)
    api_games = fetch_postseason_games(2025)

    updated = []
    for idx, row in df.iterrows():
        match = match_game(row, api_games)

        if match:
            df.at[idx, "cfbd_game_id"] = match["id"]
            df.at[idx, "home_team"] = match.get("home_team") or row["home_team"]
            df.at[idx, "away_team"] = match.get("away_team") or row["away_team"]

            # Records if available
            df.at[idx, "home_record"] = match.get("home_record") or row["home_record"]
            df.at[idx, "away_record"] = match.get("away_record") or row["away_record"]

            # Rankings (CFBD uses poll ranking objects)
            df.at[idx, "home_rank"] = match.get("home_rank") or ""
            df.at[idx, "away_rank"] = match.get("away_rank") or ""

            # Kickoff datetime
            if match.get("start_date"):
                df.at[idx, "kickoff_datetime"] = match["start_date"]

            updated.append((row["game_id"], match["id"]))

        else:
            updated.append((row["game_id"], None))

    df.to_csv(CSV_PATH, index=False)

    print("\nUPDATED MATCHES:")
    for game_id, cfbd_id in updated:
        print(f"CSV Game {game_id} → CFBD ID {cfbd_id}")

    print("\nDONE — CSV successfully updated.")


if __name__ == "__main__":
    update_csv()
