import os


LOCAL_SALT = os.environ.get("LOCAL_SALT", "a64b7eecd2d1489c9c0a4f4a317fc7d4")
SERVER_SECRET = os.getenv("SERVER_SECRET", "4f7ad55149304060adf63b59950bce17")
ACCESS_TOKEN_LIFETIME = 24 * 60 * 60
REFRESH_TOKEN_LIFETIME = 24 * 60 * 60 * 60

DB_USER = os.environ.get("DB_USER", "privacy_search")
DB_PASS = os.environ.get("DB_PASSWORD", "privacy_search")
DB_NAME = os.environ.get("DB_NAME", "privacy_search")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))

WEBSOCKET_CHANNEL = os.environ.get("WEBSOCKET_CHANNEL", "websocket_channel")
