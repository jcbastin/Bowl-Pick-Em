import pandas as pd
import requests
import os
import difflib

# ================
# CONFIG
# ================

API_KEY = os.getenv("CFBD_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

YEAR = 2025

# Paths (Render vs Local)
DISK_DIR = os.getenv("DISK_DIR", "./storage")
CSV_PATH = os.path.join(DISK_DIR, "games.csv")

# =========================================
# CFP SEEDS (Hardcoded from your bracket)
# =========================================
CFP_SEEDS = {
    "Indiana": 1,
    "Ohio State": 2,
    "Georgia": 3,
    "Texas Tech": 4,
    "Oregon": 5,
    "Ole Miss": 6,
    "Texas A&M": 7,
    "Oklahoma": 8,
    "Alabama": 9,
    "Miami": 10,
    "Tulane": 11,
    "James Madison": 12,
    "JMU": 12,  # common abbreviation
}

# Utility: Normalize names for fuzzy matching
def normalize_bowl(name):
    if not isinstance(name, str):
        return ""
    return name.lower().replace("bowl", "").replace("presented by", "").strip()


# Fetch CFBD postseason data
def fetch_cfbd_games():
    url = f"https://api.collegefootballdata.com/games?year={YEAR}&seasonType=postseason"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()


# Match our bowl name → CFBD bowl
def find_cfbd_match(bowl_name, cfbd_games):
    target = normalize_bowl(bowl_name)

    cfbd_bowl_names = {}
    for g in cfbd_games:
        name = g.get("name") or g.get("bowl_name") or ""
        cfbd_bowl_names[g["id"]] = normalize_bowl(name)

    # fuzzy match
    match = difflib.get_close_matches(target, cfbd_bowl_names.values(), n=1, cutoff=0.55)
    if not match:
        return None

    matched = match[0]

    for game_id, clean_name in cfbd_bowl_names.items():
        if clean_name == matched:
            return game_id

    return None


# Update CSV logic
def update_games_csv(csv_path):
    print(f"Loading {csv_path} ...")
    df = pd.read_csv(csv_path)
    cfbd_games = fetch_cfbd_games()

    cfbd_lookup = {g["id"]: g for g in cfbd_games}

    for idx, row in df.iterrows():
        bowl = row["bowl_name"]
        old_home = row["home_team"]
        old_away = row["away_team"]

        print(f"\nProcessing: {bowl}")

        # 1. Try to match with CFBD
        cfbd_id = find_cfbd_match(bowl, cfbd_games)
        if cfbd_id:
            game = cfbd_lookup[cfbd_id]
            print(f"Matched CFBD ID: {cfbd_id}")
            df.at[idx, "cfbd_game_id"] = cfbd_id
        else:
            print("No CFBD match found. Skipping CFBD updates.")
            continue

        # 2. If CFBD has actual teams, update them
        api_home = game.get("home_team")
        api_away = game.get("away_team")

        if api_home and api_away:
            teams_matched = {api_home, api_away} == {old_home, old_away}

            if teams_matched:
                # Correct home/away if swapped
                if old_home != api_home:
                    print("Swapping home/away to match CFBD")
                    df.at[idx, "home_team"] = api_home
                    df.at[idx, "away_team"] = api_away
                else:
                    df.at[idx, "home_team"] = api_home
                    df.at[idx, "away_team"] = api_away

            # Update records (but preserve if CFBD is missing them)
            df.at[idx, "home_record"] = game.get("home_record") or row["home_record"]
            df.at[idx, "away_record"] = game.get("away_record") or row["away_record"]

            # Apply CFP seeds if applicable
            df.at[idx, "home_rank"] = CFP_SEEDS.get(api_home, game.get("home_rank"))
            df.at[idx, "away_rank"] = CFP_SEEDS.get(api_away, game.get("away_rank"))

        else:
            print("CFBD has no teams yet → keeping your manual teams.")
            # Apply CFP ranks anyway to your manually-entered teams:
            df.at[idx, "home_rank"] = CFP_SEEDS.get(old_home, row["home_rank"])
            df.at[idx, "away_rank"] = CFP_SEEDS.get(old_away, row["away_rank"])

    # Write updated file
    df.to_csv(csv_path, index=False)
    print(f"\nUpdated bowl data saved to: {csv_path}")


# MAIN EXECUTION (For cron)
if __name__ == "__main__":
    update_games_csv(CSV_PATH)
