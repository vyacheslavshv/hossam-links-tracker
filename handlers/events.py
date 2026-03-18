from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F, Bot
from aiogram.types import ChatJoinRequest, ChatMemberUpdated, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from .filters import IsRootAdmin
from models import BotSettings, InviteLink, JoinRequest, MemberEvent

async def get_settings(bot_id: int) -> BotSettings:
    settings, _ = await BotSettings.get_or_create(bot_id=bot_id)
    return settings


async def find_invite_link(bot_id: int, url: str | None) -> InviteLink | None:
    if not url:
        return None
    return await InviteLink.get_or_none(bot_id=bot_id, url=url, revoked=False)


async def send_notification(bot: Bot, bot_config: dict, text: str, reply_markup=None):
    settings = await get_settings(bot_config["bot_id"])
    if not settings.notifications_enabled:
        return

    notif_channel = bot_config.get("notification_channel_id")
    if not notif_channel:
        return

    try:
        await bot.send_message(
            chat_id=notif_channel,
            text=text,
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


def format_join_notification(user, chat, invite_url: str | None, timestamp: str) -> str:
    name = html.escape(user.full_name)
    username = f"@{user.username}" if user.username else "N/A"
    channel_username = f"@{chat.username}" if chat.username else "N/A"
    link_display = f"<code>{html.escape(invite_url)}</code>" if invite_url else "N/A"

    return (
        f"👤 <b>New Member Joined</b>\n\n"
        f"User ID: <code>{user.id}</code>\n"
        f"Username: {username}\n"
        f"Name: {name}\n"
        f"Language: {user.language_code or 'N/A'}\n"
        f"Is Bot: {'Yes' if user.is_bot else 'No'}\n"
        f"Is Premium: {'Yes' if user.is_premium else 'No'}\n\n"
        f"📢 Channel: {html.escape(chat.title or 'Unknown')}\n"
        f"Channel ID: <code>{chat.id}</code>\n"
        f"Channel Username: {channel_username}\n"
        f"Invite Link: {link_display}\n\n"
        f"🕐 Joined: {timestamp}"
    )


def format_leave_notification(user, chat, timestamp: str) -> str:
    name = html.escape(user.full_name)
    username = f"@{user.username}" if user.username else "N/A"

    return (
        f"📤 <b>Member Left</b>\n\n"
        f"User ID: <code>{user.id}</code>\n"
        f"Username: {username}\n"
        f"Name: {name}\n\n"
        f"📢 Channel: {html.escape(chat.title or 'Unknown')}\n"
        f"Channel ID: <code>{chat.id}</code>\n\n"
        f"🕐 Left: {timestamp}"
    )


def format_request_notification(user, chat, invite_url: str | None, timestamp: str) -> str:
    name = html.escape(user.full_name)
    username = f"@{user.username}" if user.username else "N/A"
    channel_username = f"@{chat.username}" if chat.username else "N/A"
    link_display = f"<code>{html.escape(invite_url)}</code>" if invite_url else "N/A"

    return (
        f"🔔 <b>New Join Request</b>\n\n"
        f"User ID: <code>{user.id}</code>\n"
        f"Username: {username}\n"
        f"Name: {name}\n"
        f"Language: {user.language_code or 'N/A'}\n"
        f"Is Bot: {'Yes' if user.is_bot else 'No'}\n"
        f"Is Premium: {'Yes' if user.is_premium else 'No'}\n\n"
        f"📢 Channel: {html.escape(chat.title or 'Unknown')}\n"
        f"Channel ID: <code>{chat.id}</code>\n"
        f"Channel Username: {channel_username}\n"
        f"Invite Link: {link_display}\n\n"
        f"🕐 Requested: {timestamp}"
    )


# ── ChatJoinRequest handler ──

async def on_join_request(event: ChatJoinRequest, bot_config: dict):
    bot_id = bot_config["bot_id"]
    user = event.from_user
    chat = event.chat

    invite_url = event.invite_link.invite_link if event.invite_link else None
    db_link = await find_invite_link(bot_id, invite_url)

    tz = ZoneInfo(bot_config.get("timezone", "Europe/Berlin"))
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    settings = await get_settings(bot_id)

    if settings.auto_approve:
        try:
            await event.approve()
        except Exception as e:
            logger.error(f"Failed to approve join request: {e}")

        await JoinRequest.create(
            bot_id=bot_id,
            invite_link=db_link,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            status="approved",
        )
        # ChatMemberUpdated will handle the "joined" event and notification
    else:
        await JoinRequest.create(
            bot_id=bot_id,
            invite_link=db_link,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            status="pending",
        )

    logger.info(f"[{bot_id}] Join request from {user.id} ({user.full_name})")


# ── ChatMemberUpdated handler ──

async def on_chat_member_update(event: ChatMemberUpdated, bot_config: dict):
    bot_id = bot_config["bot_id"]
    user = event.new_chat_member.user
    chat = event.chat
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    tz = ZoneInfo(bot_config.get("timezone", "Europe/Berlin"))
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    invite_url = event.invite_link.invite_link if event.invite_link else None
    db_link = await find_invite_link(bot_id, invite_url)

    # ── User joined ──
    if old_status in ("left", "kicked") and new_status in ("member", "administrator"):
        # Try to find link from recent join request if not on the event
        if not db_link:
            recent_jr = await JoinRequest.filter(
                bot_id=bot_id, user_id=user.id
            ).order_by("-created_at").first()
            if recent_jr and recent_jr.invite_link_id:
                db_link = await InviteLink.get_or_none(id=recent_jr.invite_link_id)

        # Mark pending join requests as approved
        await JoinRequest.filter(
            bot_id=bot_id, user_id=user.id, status="pending"
        ).update(status="approved")

        if db_link:
            await MemberEvent.create(
                bot_id=bot_id,
                invite_link=db_link,
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                language=user.language_code,
                is_bot=user.is_bot,
                is_premium=user.is_premium or False,
                event_type="joined",
            )
            text = format_join_notification(user, chat, db_link.url, timestamp)
            await send_notification(event.bot, bot_config, text)
            logger.info(f"[{bot_id}] User {user.id} ({user.full_name}) joined via tracked link")

    # ── User left ──
    elif old_status in ("member", "administrator", "restricted") and new_status in ("left", "kicked"):
        # Find original tracked join event for this user
        join_event = await MemberEvent.filter(
            bot_id=bot_id, user_id=user.id, event_type="joined"
        ).order_by("-created_at").first()

        if join_event:
            original_link = None
            if join_event.invite_link_id:
                original_link = await InviteLink.get_or_none(id=join_event.invite_link_id)

            await MemberEvent.create(
                bot_id=bot_id,
                invite_link=original_link,
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                language=user.language_code,
                is_bot=user.is_bot,
                is_premium=user.is_premium or False,
                event_type="left",
            )
            logger.info(f"[{bot_id}] User {user.id} ({user.full_name}) left")


# ── Approve / Decline callbacks ──

async def cb_approve_request(callback: CallbackQuery, bot_config: dict):
    request_id = int(callback.data.split(":")[1])
    jr = await JoinRequest.get_or_none(id=request_id)

    if not jr or jr.bot_id != bot_config["bot_id"]:
        await callback.answer("❌ Request not found", show_alert=True)
        return

    if jr.status != "pending":
        await callback.answer("⚠️ Already processed", show_alert=True)
        return

    try:
        await callback.bot.approve_chat_join_request(
            chat_id=bot_config["channel_id"],
            user_id=jr.user_id,
        )
        jr.status = "approved"
        await jr.save()

        await callback.message.delete()
        await callback.answer("✅ Approved!")
    except Exception as e:
        logger.error(f"Failed to approve request {request_id}: {e}")
        await callback.answer(f"❌ Failed: {e}", show_alert=True)


async def cb_decline_request(callback: CallbackQuery, bot_config: dict):
    request_id = int(callback.data.split(":")[1])
    jr = await JoinRequest.get_or_none(id=request_id)

    if not jr or jr.bot_id != bot_config["bot_id"]:
        await callback.answer("❌ Request not found", show_alert=True)
        return

    if jr.status != "pending":
        await callback.answer("⚠️ Already processed", show_alert=True)
        return

    try:
        await callback.bot.decline_chat_join_request(
            chat_id=bot_config["channel_id"],
            user_id=jr.user_id,
        )
        jr.status = "declined"
        await jr.save()

        await callback.message.delete()
        await callback.answer("❌ Declined")
    except Exception as e:
        logger.error(f"Failed to decline request {request_id}: {e}")
        await callback.answer(f"❌ Failed: {e}", show_alert=True)


def create_router() -> Router:
    router = Router()
    router.chat_join_request.register(on_join_request)
    router.chat_member.register(on_chat_member_update)
    router.callback_query.register(cb_approve_request, F.data.startswith("req_approve:"), IsRootAdmin())
    router.callback_query.register(cb_decline_request, F.data.startswith("req_decline:"), IsRootAdmin())
    return router
