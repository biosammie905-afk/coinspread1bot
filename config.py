import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")  # e.g. @your_channel or -100xxxxxxxxxx

# How often to poll each source, in minutes
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))

DB_PATH = os.getenv("DB_PATH", "newsbot.db")
