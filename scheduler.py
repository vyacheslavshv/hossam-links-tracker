import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from loguru import logger

from models import InviteLink, MemberEvent


async def send_daily_report(bot: Bot, bot_config: dict):
    bot_id = bot_config["bot_id"]
    tz = ZoneInfo(bot_config.get("timezone", "Europe/Berlin"))
    now = datetime.now(tz)
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = now.replace(hour=0, minute=0, second=0, microsecond=0)

    links = await InviteLink.filter(bot_id=bot_id, revoked=False).order_by("-created_at")

    total_joined = 0
    total_left = 0
    day_joined = 0
    day_left = 0

    links_text = ""
    for link in links:
        lj = await MemberEvent.filter(invite_link=link, event_type="joined").count()
        ll = await MemberEvent.filter(invite_link=link, event_type="left").count()
        tj = await MemberEvent.filter(
            invite_link=link, event_type="joined",
            created_at__gte=yesterday_start, created_at__lt=yesterday_end,
        ).count()
        tl = await MemberEvent.filter(
            invite_link=link, event_type="left",
            created_at__gte=yesterday_start, created_at__lt=yesterday_end,
        ).count()

        total_joined += lj
        total_left += ll
        day_joined += tj
        day_left += tl

        links_text += f"   🔗 {link.name} — 👤 {lj - ll}\n"

    if not links_text:
        links_text = "   No active links\n"

    total_current = total_joined - total_left
    net = day_joined - day_left
    report_date = yesterday_start.strftime('%Y-%m-%d')

    channel_title = bot_config.get("channel_title", "Unknown")

    text = (
        f"📊 <b>Daily Report — {report_date}</b>\n\n"
        f"📢 Channel: {channel_title}\n\n"
        f"📈 <b>Day Activity:</b>\n"
        f"   New Joins: {day_joined}\n"
        f"   Leaves: {day_left}\n"
        f"   Net Growth: {'+' if net >= 0 else ''}{net}\n\n"
        f"📋 <b>Links Overview:</b>\n"
        f"{links_text}\n"
        f"👥 Total Members: <b>{total_current}</b>"
    )

    for admin_id in bot_config.get("admin_ids", []):
        try:
            await bot.send_message(chat_id=admin_id, text=text)
        except Exception as e:
            logger.error(f"Failed to send daily report to {admin_id}: {e}")


async def scheduler_loop(bot: Bot, bot_config: dict):
    tz = ZoneInfo(bot_config.get("timezone", "Europe/Berlin"))

    while True:
        now = datetime.now(tz)
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_seconds = (next_midnight - now).total_seconds()

        logger.info(
            f"[@{bot_config.get('bot_username', '?')}] "
            f"Next daily report in {sleep_seconds / 3600:.1f}h"
        )

        await asyncio.sleep(sleep_seconds)

        try:
            await send_daily_report(bot, bot_config)
            logger.info(f"[@{bot_config.get('bot_username', '?')}] Daily report sent")
        except Exception as e:
            logger.error(f"[@{bot_config.get('bot_username', '?')}] Daily report failed: {e}")
