import os


LOCAL_SALT = os.environ.get("LOCAL_SALT", "a64b7eecd2d1489c9c0a4f4a317fc7d4")
SERVER_SECRET = os.getenv("SERVER_SECRET", "4f7ad55149304060adf63b59950bce17")
ACCESS_TOKEN_LIFETIME = 24 * 60 * 60
REFRESH_TOKEN_LIFETIME = 24 * 60 * 60 * 60

BASEDIR = os.path.dirname(os.path.abspath(__file__))

DB_USER = os.environ.get("DB_USER", "privacy_search")
DB_PASS = os.environ.get("DB_PASSWORD", "privacy_search")
DB_NAME = os.environ.get("DB_NAME", "privacy_search")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))

WEBSOCKET_CHANNEL = os.environ.get("WEBSOCKET_CHANNEL", "websocket_channel")

USE_TELETHON = bool(int(os.environ.get("USE_TELETHON", 0)))
TG_API_ID = os.environ.get("TG_API_ID")
TG_API_HASH = os.environ.get("TG_API_HASH")
TG_PHONE = os.environ.get("TG_PHONE")
if USE_TELETHON:
    if not TG_API_ID:
        raise Exception("TG_API_ID not defined")
    if not TG_API_HASH:
        raise Exception("TG_API_HASH not defined")
    if not TG_PHONE:
        raise Exception("TG_PHONE not defined")
TELETHON_SESSION = os.environ.get("TELETHON_SESSION", "osint_operator")

REDIS_URI = os.environ.get("REDIS_URI", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_DB = os.environ.get("REDIS_DB", 0)
REDIS_PUBSUB_DB = os.environ.get("REDIS_PUBSUB_DB", 2)

try:
    DEBUG = bool(int(os.environ.get("DEBUG", 0)))
except Exception:
    DEBUG = False

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)
