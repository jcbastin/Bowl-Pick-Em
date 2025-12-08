import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer " + API_KEY}

CSV_PATH = "storage_seed/games.csv"

# ----------------------------------------------------
# 1. Fetch all team records for a given year
# ----------------------------------------------------
def fetch_records(year):
    url = "https://api.collegefootballdata.com/records"
    r = requests.get(url, headers=HEADERS, params={"year": year})

    if r.status_code != 200:
        print("Record API Error:", r.status_code)
        return {}

    records = {}
    for team in r.json():
        name = team["team"]
        wins = team["total"]["wins"]
        losses = team["total"]["losses"]
        records[name] = f"{wins}-{losses}"
    return records


# ----------------------------------------------------
# 2. Fetch AP/CFP rankings for the season
# ----------------------------------------------------
def fetch_rankings(year):
    url = "https://api.collegefootballdata.com/rankings"
    r = requests.get(url, headers=HEADERS, params={"year": year})

    if r.status_code != 200:
        print("Rankings API Error:", r.status_code)
        return {}

    team_ranks = {}

    data = r.json()
    for week in data:
        for poll in week["polls"]:
            if poll["poll"] == "AP Top 25":  # choose AP, but you can switch
                for entry in poll["ranks"]:
                    team_ranks[entry["school"]] = entry["rank"]

    return team_ranks


# ----------------------------------------------------
# Main script
# ----------------------------------------------------
def main():
    df = pd.read_csv(CSV_PATH)

    df["away_team"] = df["away_team"].astype(str)
    df["home_team"] = df["home_team"].astype(str)

    # Determine relevant years from kickoff dates
    df["year"] = df["kickoff_datetime"].str[:4].astype(int)
    years = df["year"].unique()

    # Preload all years
    year_records = {}
    year_ranks = {}

    for y in years:
        print(f"Fetching CFBD data for {y}...")
        year_records[y] = fetch_records(y)
        year_ranks[y] = fetch_rankings(y)

    # Ensure columns exist
    for col in ["away_record", "home_record", "away_rank", "home_rank"]:
        if col not in df.columns:
            df[col] = ""

    # Fill the CSV
    for idx, row in df.iterrows():
        y = row["year"]

        away = row["away_team"]
        home = row["home_team"]

        df.loc[idx, "away_record"] = year_records[y].get(away, "")
        df.loc[idx, "home_record"] = year_records[y].get(home, "")

        df.loc[idx, "away_rank"] = year_ranks[y].get(away, "")
        df.loc[idx, "home_rank"] = year_ranks[y].get(home, "")

        print(f"Updated {row['bowl_name']} → {away} / {home}")

    df.drop(columns=["year"], inplace=True)
    df.to_csv(CSV_PATH, index=False)
    print("DONE — updated:", CSV_PATH)


if __name__ == "__main__":
    main()
