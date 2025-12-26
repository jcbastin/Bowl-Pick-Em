import pandas as pd
import requests
import os

# ======================================================
#               CONFIG
# ======================================================

API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

CSV_PATH = "/opt/render/project/src/storage/games.csv"


# ======================================================
#               HELPERS
# ======================================================

def normalize_team(name: str) -> str:
    """
    Normalize team names so punctuation differences
    (e.g. Hawai'i vs Hawaii) never break scoring.
    """
    if not isinstance(name, str):
        return ""
    return (
        name.lower()
        .replace("’", "'")
        .replace("'", "")
        .replace(".", "")
        .strip()
    )


def fetch_postseason_games():
    """
    Fetch ALL postseason games for 2025.
    CFBD assigns postseason games a seasonType of 'postseason'.
    """
    try:
        resp = requests.get(
            "https://api.collegefootballdata.com/games",
            params={"year": 2025, "seasonType": "postseason"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"⚠️ Error contacting CFBD API: {e}")
        return None


# ======================================================
#               MAIN
# ======================================================

def main():
    print("🔄 Running update_winners_live for POSTSEASON 2025...")

    # Load games.csv
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"❌ Failed to read CSV: {CSV_PATH} → {e}")
        return

    # Defensive column setup
    for col in ["winner", "completed", "home_score", "away_score"]:
        if col not in df.columns:
            df[col] = ""

    df["completed"] = df["completed"].astype(bool)

    # Fetch CFBD data
    games = fetch_postseason_games()
    if not games:
        print("⚠️ No API data returned.")
        return

    # Lookup by CFBD ID
    cfbd_lookup = {g["id"]: g for g in games}

    updated_any = False

    for idx, row in df.iterrows():
        cfbd_id = row.get("cfbd_game_id")

        if pd.isna(cfbd_id):
            continue

        try:
            cfbd_id = int(cfbd_id)
        except Exception:
            continue

        match = cfbd_lookup.get(cfbd_id)
        if match is None:
            continue

        # Skip unplayed games
        if not match.get("completed", False):
            continue

        home = match.get("homeTeam")
        away = match.get("awayTeam")
        home_pts = match.get("homePoints")
        away_pts = match.get("awayPoints")

        if home_pts is None or away_pts is None:
            continue

        # Determine raw winner
        raw_winner = home if home_pts > away_pts else away

        # ✅ NORMALIZE BEFORE WRITING
        winner = normalize_team(raw_winner)

        # Normalize existing CSV value for comparison
        existing_winner = normalize_team(df.loc[idx, "winner"])

        if (
            existing_winner != winner
            or df.loc[idx, "completed"] is False
            or df.loc[idx, "home_score"] != home_pts
            or df.loc[idx, "away_score"] != away_pts
        ):
            print(f"✔ UPDATED: {away} vs {home} → {raw_winner}")

            df.loc[idx, "winner"] = winner
            df.loc[idx, "completed"] = True
            df.loc[idx, "home_score"] = home_pts
            df.loc[idx, "away_score"] = away_pts

            updated_any = True

    # Save updates
    if updated_any:
        try:
            df.to_csv(CSV_PATH, index=False)
            print("💾 CSV updated successfully.")
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")
    else:
        print("ℹ️ No updates needed.")

    print("✅ update_winners_live POSTSEASON completed.")


if __name__ == "__main__":
    main()
