import os
import requests
import pandas as pd

# ---- Paths ----
CSV_PATH = "/opt/render/project/src/storage/games.csv"

# ---- CFBD Key ----
CFBD_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer {CFBD_KEY}"}

# ---- Provider Priority ----
PROVIDER_PRIORITY = ["DraftKings", "Bovada"]


def choose_spread(lines):
    """
    Select spread using priority (DraftKings -> Bovada -> first available).
    """
    # Priority providers
    for provider in PROVIDER_PRIORITY:
        for item in lines:
            if item.get("provider") == provider and item.get("spread") is not None:
                return item["spread"]

    # Fallback: first available spread
    for item in lines:
        if item.get("spread") is not None:
            return item["spread"]

    return None


def main():
    df = pd.read_csv(CSV_PATH)

    if CFBD_KEY is None:
        print("ERROR: CFBD_API_KEY is missing.")
        return

    updated_count = 0

    for idx, row in df.iterrows():
        game_id = row.get("cfbd_game_id")

        # skip missing IDs
        if pd.isna(game_id):
            continue

        url = f"https://api.collegefootballdata.com/lines?gameId={int(game_id)}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"[{game_id}] CFBD ERROR:", response.text)
            continue

        data = response.json()

        if not data or "lines" not in data[0] or not data[0]["lines"]:
            print(f"[{game_id}] No line data found")
            continue

        spread = choose_spread(data[0]["lines"])

        print(f"{row['away_team']} vs {row['home_team']} -> spread: {spread}")

        df.at[idx, "spread"] = spread
        updated_count += 1

    df.to_csv(CSV_PATH, index=False)
    print(f"Completed spread update for {updated_count} games.")


if __name__ == "__main__":
    main()
