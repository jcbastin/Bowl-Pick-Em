import pandas as pd
from tabulate import tabulate

CSV_PATH = "storage_seed/games.csv"   # adjust if needed


def safe(v):
    """Return empty string instead of NaN."""
    if pd.isna(v):
        return ""
    return v


def main():
    df = pd.read_csv(CSV_PATH)

    print("\n==================== BOWL GAME INSPECTION ====================\n")

    for idx, row in df.iterrows():

        block = [
            ["Game ID", safe(row["game_id"])],
            ["Bowl Name", safe(row["bowl_name"])],
            ["Kickoff", safe(row["kickoff_datetime"])],
            ["Point Value", safe(row["point_value"])],
            ["Away Team", safe(row["away_team"])],
            ["Home Team", safe(row["home_team"])],
            ["Away Record", safe(row.get("away_record", ""))],
            ["Home Record", safe(row.get("home_record", ""))],
            ["Away Rank", safe(row.get("away_rank", ""))],
            ["Home Rank", safe(row.get("home_rank", ""))],
            ["Status", safe(row["status"])],
            ["Winner", safe(row["winner"])],
            ["Completed", safe(row["completed"])],
            ["Away Score", safe(row["away_score"])],
            ["Home Score", safe(row["home_score"])],
            ["CFBD Game ID", safe(row.get("cfbd_game_id", ""))],
            ["Location", safe(row["location"])],
            ["Network", safe(row["network"])],
            ["Spread", safe(row["spread"])],
        ]

        print(tabulate(block, tablefmt="fancy_grid"))
        print("\n--------------------------------------------------------------\n")


if __name__ == "__main__":
    main()
