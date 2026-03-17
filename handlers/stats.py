from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from .filters import IsAdmin
from models import InviteLink, MemberEvent, JoinRequest

router = Router()


@router.callback_query(F.data == "stats", IsAdmin())
async def cb_stats(callback: CallbackQuery, bot_config: dict):
    bot_id = bot_config["bot_id"]
    tz = ZoneInfo(bot_config.get("timezone", "Europe/Berlin"))

    total_joined = await MemberEvent.filter(bot_id=bot_id, event_type="joined").count()
    total_left = await MemberEvent.filter(bot_id=bot_id, event_type="left").count()
    total_pending = await JoinRequest.filter(bot_id=bot_id, status="pending").count()
    total_current = total_joined - total_left

    today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    today_joined = await MemberEvent.filter(
        bot_id=bot_id, event_type="joined", created_at__gte=today
    ).count()
    today_left = await MemberEvent.filter(
        bot_id=bot_id, event_type="left", created_at__gte=today
    ).count()
    net = today_joined - today_left

    links = await InviteLink.filter(bot_id=bot_id, revoked=False).order_by("-created_at")

    text = (
        f"📊 <b>Overall Statistics</b>\n\n"
        f"👤 Current Members: <b>{total_current}</b>\n"
        f"📥 Total Joined: {total_joined}\n"
        f"📤 Total Left: {total_left}\n"
        f"⏳ Pending Requests: {total_pending}\n\n"
        f"📈 <b>Today:</b>\n"
        f"   📥 Joined: {today_joined}\n"
        f"   📤 Left: {today_left}\n"
        f"   📊 Net: {'+' if net >= 0 else ''}{net}"
    )

    buttons = []
    for link in links:
        joined = await MemberEvent.filter(invite_link=link, event_type="joined").count()
        left = await MemberEvent.filter(invite_link=link, event_type="left").count()
        current = joined - left
        buttons.append([InlineKeyboardButton(
            text=f"🔗 {link.name} — 👤 {current}",
            callback_data=f"stats_link:{link.id}",
        )])
    buttons.append([InlineKeyboardButton(text="🔄 Refresh", callback_data="stats")])
    buttons.append([InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stats_link:"), IsAdmin())
async def cb_stats_link(callback: CallbackQuery, bot_config: dict):
    link_id = int(callback.data.split(":")[1])
    link = await InviteLink.get_or_none(id=link_id, bot_id=bot_config["bot_id"])

    if not link:
        await callback.answer("❌ Link not found", show_alert=True)
        return

    joined = await MemberEvent.filter(invite_link=link, event_type="joined").count()
    left = await MemberEvent.filter(invite_link=link, event_type="left").count()
    pending = await JoinRequest.filter(invite_link=link, status="pending").count()
    declined = await JoinRequest.filter(invite_link=link, status="declined").count()
    current = joined - left

    text = (
        f"📊 <b>Tracking Statistics</b>\n\n"
        f"🔗 Name: {link.name}\n"
        f"🔗 URL: <code>{link.url}</code>\n"
        f"⏳ Pending Requests: {pending}\n"
        f"🚫 Declined: {declined}\n"
        f"📥 Joined: {joined}\n"
        f"📤 Left: {left}\n"
        f"👤 Current: {current}"
    )

    buttons = [
        [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"stats_link:{link.id}")],
        [InlineKeyboardButton(text="🔙 All Stats", callback_data="stats")],
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()
