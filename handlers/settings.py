from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from .filters import IsRootAdmin
from models import BotSettings, JoinRequest

router = Router()


async def get_settings(bot_id: int) -> BotSettings:
    settings, _ = await BotSettings.get_or_create(bot_id=bot_id)
    return settings


async def show_settings(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    pending_count = await JoinRequest.filter(
        bot_id=bot_config["bot_id"], status="pending"
    ).count()

    auto_icon = "✅" if settings.auto_approve else "❌"
    notif_icon = "✅" if settings.notifications_enabled else "❌"

    notif_channel = bot_config.get("notification_channel_id")
    channel_display = f"<code>{notif_channel}</code>" if notif_channel else "Not set"

    text = (
        f"⚙️ <b>Settings</b>\n\n"
        f"📢 Member Info Channel: {channel_display}\n"
        f"⏳ Pending Requests: <b>{pending_count}</b>\n\n"
        f"Toggle options:"
    )

    buttons = [
        [InlineKeyboardButton(
            text=f"{auto_icon} Auto-approve join requests",
            callback_data="toggle:auto_approve",
        )],
        [InlineKeyboardButton(
            text=f"{notif_icon} Notifications to channel",
            callback_data="toggle:notifications",
        )],
        [InlineKeyboardButton(
            text=f"🗑 Clear Pending Requests ({pending_count})",
            callback_data="clear_pending",
        )],
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "settings", IsRootAdmin())
async def cb_settings(callback: CallbackQuery, bot_config: dict):
    await show_settings(callback, bot_config)
    await callback.answer()


@router.callback_query(F.data == "toggle:auto_approve", IsRootAdmin())
async def cb_toggle_auto_approve(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    settings.auto_approve = not settings.auto_approve
    await settings.save()

    status = "enabled ✅" if settings.auto_approve else "disabled ❌"
    await show_settings(callback, bot_config)
    await callback.answer(f"Auto-approve {status}")


@router.callback_query(F.data == "toggle:notifications", IsRootAdmin())
async def cb_toggle_notifications(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    settings.notifications_enabled = not settings.notifications_enabled
    await settings.save()

    status = "enabled ✅" if settings.notifications_enabled else "disabled ❌"
    await show_settings(callback, bot_config)
    await callback.answer(f"Notifications {status}")


@router.callback_query(F.data == "clear_pending", IsRootAdmin())
async def cb_clear_pending(callback: CallbackQuery, bot_config: dict):
    deleted = await JoinRequest.filter(
        bot_id=bot_config["bot_id"], status="pending"
    ).delete()

    if deleted:
        # Also try to decline them in Telegram
        # (they may have already expired, so we just clear DB)
        await callback.answer(f"🗑 Cleared {deleted} pending request(s)")
    else:
        await callback.answer("No pending requests to clear")

    await show_settings(callback, bot_config)
