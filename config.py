import os
from dotenv import load_dotenv

load_dotenv()  # local .env; Railway par Variables use hote hain

BOT_TOKEN = os.environ["BOT_TOKEN"]
MONGO_URI = os.environ["MONGO_URI"]
OWNER_ID = int(os.environ["OWNER_ID"])
DB_NAME = os.getenv("DB_NAME", "giveaway_bot")

# Optional: start screen banner (image URL or Telegram file_id)
BANNER = os.getenv("BANNER", "")
DEFAULT_TITLE = "Vote for your favorite!"
