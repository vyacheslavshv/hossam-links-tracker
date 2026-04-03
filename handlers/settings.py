from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from .filters import IsRootAdmin
from models import BotSettings, InviteLink, JoinRequest


async def get_settings(bot_id: int) -> BotSettings:
    settings, _ = await BotSettings.get_or_create(bot_id=bot_id)
    return settings


async def build_settings_content(bot_config: dict) -> tuple[str, InlineKeyboardMarkup]:
    settings = await get_settings(bot_config["bot_id"])

    auto_icon = "✅" if settings.auto_approve else "❌"
    notif_icon = "✅" if settings.notifications_enabled else "❌"

    notif_channel = bot_config.get("notification_channel_id")
    channel_display = f"<code>{notif_channel}</code>" if notif_channel else "Not set"

    text = (
        f"⚙️ <b>Settings</b>\n\n"
        f"📢 Member Info Channel: {channel_display}\n\n"
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
    ]

    active_links = await InviteLink.filter(bot_id=bot_config["bot_id"], revoked=False)
    pending_count = 0
    if active_links:
        pending_count = await JoinRequest.filter(
            invite_link__in=active_links, status="pending"
        ).count()
    if pending_count > 0:
        buttons.append([InlineKeyboardButton(
            text=f"🧹 Reset pending requests ({pending_count})",
            callback_data="reset_pending",
        )])

    links = await InviteLink.filter(bot_id=bot_config["bot_id"], revoked=False).order_by("-created_at")
    if links:
        for link in links:
            buttons.append([InlineKeyboardButton(
                text=f"🗑 Delete: {link.name}",
                callback_data=f"del_link:{link.id}",
            )])

    return text, InlineKeyboardMarkup(inline_keyboard=buttons)


async def cb_settings(callback: CallbackQuery, bot_config: dict):
    text, markup = await build_settings_content(bot_config)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


async def msg_settings(message: Message, bot_config: dict):
    text, markup = await build_settings_content(bot_config)
    await message.answer(text, reply_markup=markup)


async def cb_toggle_auto_approve(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    settings.auto_approve = not settings.auto_approve
    await settings.save()

    status = "enabled ✅" if settings.auto_approve else "disabled ❌"
    text, markup = await build_settings_content(bot_config)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer(f"Auto-approve {status}")


async def cb_toggle_notifications(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    settings.notifications_enabled = not settings.notifications_enabled
    await settings.save()

    status = "enabled ✅" if settings.notifications_enabled else "disabled ❌"
    text, markup = await build_settings_content(bot_config)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer(f"Notifications {status}")


async def cb_delete_link(callback: CallbackQuery, bot_config: dict):
    link_id = int(callback.data.split(":")[1])
    link = await InviteLink.get_or_none(id=link_id, bot_id=bot_config["bot_id"])

    if not link:
        await callback.answer("❌ Link not found", show_alert=True)
        return

    try:
        await callback.bot.revoke_chat_invite_link(
            chat_id=bot_config["channel_id"],
            invite_link=link.url,
        )
    except Exception as e:
        logger.warning(f"Could not revoke link in Telegram: {e}")

    link.revoked = True
    await link.save()

    await callback.answer(f"🗑 Link \"{link.name}\" deleted")

    text, markup = await build_settings_content(bot_config)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass


async def cb_reset_pending_confirm(callback: CallbackQuery, bot_config: dict):
    active_links = await InviteLink.filter(bot_id=bot_config["bot_id"], revoked=False)
    pending_count = 0
    if active_links:
        pending_count = await JoinRequest.filter(
            invite_link__in=active_links, status="pending"
        ).count()
    if pending_count == 0:
        await callback.answer("No pending requests", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"✅ Yes, reset {pending_count}", callback_data="reset_pending_yes"),
            InlineKeyboardButton(text="❌ No", callback_data="settings"),
        ],
    ])
    await callback.message.edit_text(
        f"Are you sure you want to reset <b>{pending_count}</b> pending requests?",
        reply_markup=keyboard,
    )
    await callback.answer()


async def cb_reset_pending_yes(callback: CallbackQuery, bot_config: dict):
    active_links = await InviteLink.filter(bot_id=bot_config["bot_id"], revoked=False)
    deleted = 0
    if active_links:
        deleted = await JoinRequest.filter(
            invite_link__in=active_links, status="pending"
        ).delete()

    await callback.answer(f"🧹 {deleted} pending requests removed", show_alert=True)

    text, markup = await build_settings_content(bot_config)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass


def create_router() -> Router:
    router = Router()
    router.callback_query.register(cb_settings, F.data == "settings", IsRootAdmin())
    router.message.register(msg_settings, F.text == "⚙️ Settings", IsRootAdmin())
    router.callback_query.register(cb_toggle_auto_approve, F.data == "toggle:auto_approve", IsRootAdmin())
    router.callback_query.register(cb_toggle_notifications, F.data == "toggle:notifications", IsRootAdmin())
    router.callback_query.register(cb_delete_link, F.data.startswith("del_link:"), IsRootAdmin())
    router.callback_query.register(cb_reset_pending_confirm, F.data == "reset_pending", IsRootAdmin())
    router.callback_query.register(cb_reset_pending_yes, F.data == "reset_pending_yes", IsRootAdmin())
    return router
