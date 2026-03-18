"""
Send daily report from all bots to a specific user.
Run: python send_report.py
"""
import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from tortoise import Tortoise

from config import load_bots_config, TORTOISE_ORM
from scheduler import send_daily_report

MY_ID = 5418853660


async def main():
    await Tortoise.init(config=TORTOISE_ORM)

    bots_config = load_bots_config()

    for cfg in bots_config:
        bot = Bot(
            token=cfg["bot_token"],
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        me = await bot.get_me()
        cfg["bot_id"] = me.id
        cfg["bot_username"] = me.username

        try:
            chat = await bot.get_chat(cfg["channel_id"])
            cfg["channel_title"] = chat.title
        except Exception:
            cfg["channel_title"] = "Unknown"

        # Override admin_ids to send only to me
        original_admins = cfg["admin_ids"]
        cfg["admin_ids"] = [MY_ID]

        try:
            await send_daily_report(bot, cfg)
            print(f"✅ @{me.username} — report sent")
        except Exception as e:
            print(f"❌ @{me.username} — failed: {e}")

        cfg["admin_ids"] = original_admins
        await bot.session.close()

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
