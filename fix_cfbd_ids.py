import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer " + API_KEY}

CSV_PATH = "storage_seed/games.csv"

# -----------------------------
# Normalization Helpers
# -----------------------------
def normalize(s):
    if not isinstance(s, str):
        return ""
    return "".join(c.lower() for c in s if c.isalnum())


def tokenize(s):
    return set(normalize(s).split())


def similarity(a, b):
    """Simple fuzzy similarity: Jaccard between word sets."""
    if not a or not b:
        return 0
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0
    return len(ta & tb) / len(ta | tb)


# -----------------------------
# CFBD Fetch
# -----------------------------
def fetch_postseason(year):
    url = "https://api.collegefootballdata.com/games"
    params = {"year": year, "seasonType": "postseason"}
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        print("API error:", r.status_code)
        return []
    return r.json()


# -----------------------------
# Main Matching Logic
# -----------------------------
def main():
    df = pd.read_csv(CSV_PATH)

    df["year"] = df["kickoff_datetime"].str[:4].astype(int)
    years = df["year"].unique()

    cfbd_data = {}
    for y in years:
        print(f"Fetching CFBD postseason games for {y}...")
        cfbd_data[y] = fetch_postseason(y)

    if "cfbd_game_id" not in df.columns:
        df["cfbd_game_id"] = ""

    for idx, row in df.iterrows():
        y = row["year"]
        bowl_csv = row["bowl_name"]
        bowl_norm = normalize(bowl_csv)
        home_norm = normalize(row["home_team"])
        away_norm = normalize(row["away_team"])
        kickoff_csv = row["kickoff_datetime"].replace(" ", "T")

        candidates = cfbd_data[y]
        matched_id = None

        # --------------------------
        # 1. Exact bowl name match
        # --------------------------
        for g in candidates:
            if normalize(g.get("notes")) == bowl_norm:
                matched_id = g["id"]
                break

        # --------------------------
        # 2. Exact home/away match
        # --------------------------
        if matched_id is None:
            for g in candidates:
                if (
                    normalize(g.get("homeTeam")) == home_norm
                    and normalize(g.get("awayTeam")) == away_norm
                ):
                    matched_id = g["id"]
                    break

        # --------------------------
        # 3. Kickoff datetime match
        # --------------------------
        if matched_id is None:
            for g in candidates:
                api_time = str(g.get("startDate", "")).replace("Z", "")
                if api_time.startswith(kickoff_csv):
                    matched_id = g["id"]
                    break

        # --------------------------
        # 4. FUZZY bowl-name match
        # --------------------------
        if matched_id is None:
            best_score = 0
            best_id = None

            for g in candidates:
                api_bowl = g.get("notes", "")
                score = similarity(api_bowl, bowl_csv)
                if score > best_score:
                    best_score = score
                    best_id = g["id"]

            # Accept if similarity is high enough
            if best_score >= 0.35:
                matched_id = best_id

        # --------------------------
        # Save result
        # --------------------------
        if matched_id:
            print(f"Matched {bowl_csv} → {matched_id}")
            df.loc[idx, "cfbd_game_id"] = matched_id
        else:
            print(f"WARNING: Could not match: {bowl_csv}")

    df.drop(columns=["year"], inplace=True)
    df.to_csv(CSV_PATH, index=False)
    print("\nDONE — Fuzzy-matched CFBD game IDs written.\n")


if __name__ == "__main__":
    main()
