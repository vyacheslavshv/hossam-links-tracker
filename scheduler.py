import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from loguru import logger

from models import InviteLink, MemberEvent, JoinRequest


async def send_daily_report(bot: Bot, bot_config: dict):
    bot_id = bot_config["bot_id"]
    tz = ZoneInfo(bot_config.get("timezone", "Europe/Berlin"))
    now = datetime.now(tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_joined = await MemberEvent.filter(bot_id=bot_id, event_type="joined").count()
    total_left = await MemberEvent.filter(bot_id=bot_id, event_type="left").count()
    total_current = total_joined - total_left

    today_joined = await MemberEvent.filter(
        bot_id=bot_id, event_type="joined", created_at__gte=today_start
    ).count()
    today_left = await MemberEvent.filter(
        bot_id=bot_id, event_type="left", created_at__gte=today_start
    ).count()
    net = today_joined - today_left

    links = await InviteLink.filter(bot_id=bot_id, revoked=False).order_by("-created_at")

    links_text = ""
    for link in links:
        lj = await MemberEvent.filter(invite_link=link, event_type="joined").count()
        ll = await MemberEvent.filter(invite_link=link, event_type="left").count()
        links_text += f"   🔗 {link.name} — 👤 {lj - ll}\n"

    if not links_text:
        links_text = "   No active links\n"

    channel_title = bot_config.get("channel_title", "Unknown")

    text = (
        f"📊 <b>Daily Report — {now.strftime('%Y-%m-%d')}</b>\n\n"
        f"📢 Channel: {channel_title}\n\n"
        f"📈 <b>Today's Activity:</b>\n"
        f"   New Joins: {today_joined}\n"
        f"   Leaves: {today_left}\n"
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
