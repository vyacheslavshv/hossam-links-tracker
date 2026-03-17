from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from .filters import IsRootAdmin
from models import BotSettings


async def get_settings(bot_id: int) -> BotSettings:
    settings, _ = await BotSettings.get_or_create(bot_id=bot_id)
    return settings


def build_settings_content(settings: BotSettings, bot_config: dict) -> tuple[str, InlineKeyboardMarkup]:
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
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
    ]

    return text, InlineKeyboardMarkup(inline_keyboard=buttons)


async def cb_settings(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    text, markup = build_settings_content(settings, bot_config)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


async def msg_settings(message: Message, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    text, markup = build_settings_content(settings, bot_config)
    await message.answer(text, reply_markup=markup)


async def cb_toggle_auto_approve(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    settings.auto_approve = not settings.auto_approve
    await settings.save()

    status = "enabled ✅" if settings.auto_approve else "disabled ❌"
    text, markup = build_settings_content(settings, bot_config)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer(f"Auto-approve {status}")


async def cb_toggle_notifications(callback: CallbackQuery, bot_config: dict):
    settings = await get_settings(bot_config["bot_id"])
    settings.notifications_enabled = not settings.notifications_enabled
    await settings.save()

    status = "enabled ✅" if settings.notifications_enabled else "disabled ❌"
    text, markup = build_settings_content(settings, bot_config)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer(f"Notifications {status}")


def create_router() -> Router:
    router = Router()
    router.callback_query.register(cb_settings, F.data == "settings", IsRootAdmin())
    router.message.register(msg_settings, F.text == "⚙️ Settings", IsRootAdmin())
    router.callback_query.register(cb_toggle_auto_approve, F.data == "toggle:auto_approve", IsRootAdmin())
    router.callback_query.register(cb_toggle_notifications, F.data == "toggle:notifications", IsRootAdmin())
    return router
