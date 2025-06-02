import os
import sys
from typing import List

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))  # Render uses port 10000 by default
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Determine base URL based on environment
if RENDER_EXTERNAL_URL:
    BASE_URL = RENDER_EXTERNAL_URL
else:
    # Fallback for local development
    BASE_URL = f"http://localhost:{PORT}"

# Admin IDs from environment
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: List[int] = []
if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip()]
    except ValueError:
        print("[ERROR] Invalid ADMIN_IDS format. Should be comma-separated integers.")
        sys.exit(1)

# Validation
if not BOT_TOKEN:
    print("[ERROR] BOT_TOKEN is not set!")
    sys.exit(1)

# Webhook configuration
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use SQLite for local development
    DATABASE_URL = "sqlite+aiosqlite:///corporate_bot.db"
elif DATABASE_URL.startswith("postgresql://"):
    # Convert PostgreSQL URL for async support and handle SSL properly
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Replace sslmode parameter with proper asyncpg format
    if "?sslmode=require" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("?sslmode=require", "")

print(f"[CONFIG] Using PORT={PORT}, WEBHOOK_URL={WEBHOOK_URL}")
print(f"[CONFIG] Admin IDs: {ADMIN_IDS}")
print(f"[CONFIG] Environment: {ENVIRONMENT}")
