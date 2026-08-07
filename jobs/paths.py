import os

# Mirrors the DISK_DIR logic in app.py so jobs read/write the same files
# whether they run on Render's persistent disk or locally.
if os.getenv("RENDER"):
    DISK_DIR = "/opt/render/project/src/storage"
else:
    DISK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")
    os.makedirs(DISK_DIR, exist_ok=True)

GAMES_CSV = os.path.join(DISK_DIR, "games.csv")
