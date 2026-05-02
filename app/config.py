from dotenv import load_dotenv
import os

load_dotenv()

JELLYFIN_URL = os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
RADARR_URL = os.getenv("RADARR_URL")
RADARR_API_KEY = os.getenv("RADARR_API_KEY")

required_env_vars = {
    "JELLYFIN_URL": JELLYFIN_URL,
    "JELLYFIN_API_KEY": JELLYFIN_API_KEY,
    "RADARR_URL": RADARR_URL,
    "RADARR_API_KEY": RADARR_API_KEY,
}

missing = [name for name, value in required_env_vars.items() if not value]

if missing:
    raise RuntimeError(
        "Missing required environment variables: "
        + ", ".join(missing)
        + ". Check your .env file."
    )
