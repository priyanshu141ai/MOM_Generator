import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.bots.google_meet import open_google_login


if __name__ == "__main__":
    asyncio.run(open_google_login())
