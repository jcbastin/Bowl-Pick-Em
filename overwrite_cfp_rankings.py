import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer " + API_KEY}

CSV_PATH = "storage_seed/games.csv"


def fetch_cfp_rankings(year):
    """Return a dict: team → CFP rank."""
    url = "https://api.collegefootballdata.com/rankings"
    r = requests.get(url, headers=HEADERS, params={"year": year})

    if r.status_code != 200:
        print("CFP ranking error:", r.status_code)
        return {}

    rankings = {}

    for week in r.json():
        for poll in week["polls"]:
            if poll["poll"] == "College Football Playoff Rankings":
                for entry in poll["ranks"]:
                    school = entry["school"]
                    rankings[school] = entry["rank"]

    return rankings


def main():
    df = pd.read_csv(CSV_PATH)

    df["year"] = df["kickoff_datetime"].str[:4].astype(int)
    years = df["year"].unique()

    year_cfp_ranks = {}

    for y in years:
        print(f"Fetching CFP rankings for {y}...")
        year_cfp_ranks[y] = fetch_cfp_rankings(y)

    for idx, row in df.iterrows():

        y = row["year"]
        cfp = year_cfp_ranks[y]

        away = row["away_team"]
        home = row["home_team"]

        df.loc[idx, "away_rank"] = cfp.get(away, "")
        df.loc[idx, "home_rank"] = cfp.get(home, "")

        print(f"Updated {row['bowl_name']}: {away} vs {home}")

    df.drop(columns=["year"], inplace=True)
    df.to_csv(CSV_PATH, index=False)

    print("\nDONE — CFP rankings applied.\n")


if __name__ == "__main__":
    main()
