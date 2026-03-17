import os
import json
from dotenv import load_dotenv

load_dotenv()

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://data/db.sqlite3")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Berlin")


def load_bots_config() -> list[dict]:
    with open("bots.json", "r") as f:
        bots = json.load(f)
    for bot_cfg in bots:
        if "admin_ids" not in bot_cfg:
            bot_cfg["admin_ids"] = ADMIN_IDS
        else:
            bot_cfg["admin_ids"] = list(set(bot_cfg["admin_ids"] + ADMIN_IDS))
        bot_cfg.setdefault("notification_channel_id", None)
        bot_cfg.setdefault("timezone", TIMEZONE)
    return bots


TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
