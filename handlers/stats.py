from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from .filters import IsAdmin, IsRootAdmin, is_root_admin
from models import InviteLink, MemberEvent, JoinRequest


async def build_stats(bot_config: dict, root: bool) -> tuple[str, InlineKeyboardMarkup]:
    bot_id = bot_config["bot_id"]
    links = await InviteLink.filter(bot_id=bot_id, revoked=False).order_by("-created_at")

    if not links:
        text = "📊 <b>Tracking Statistics</b>\n\nNo active links found."
        buttons = [
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="stats")],
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=buttons)

    total_pending = 0
    total_declined = 0
    total_joined = 0
    total_left = 0

    parts = ["📊 <b>Tracking Statistics</b>"]
    delete_buttons = []

    for link in links:
        joined = await MemberEvent.filter(invite_link=link, event_type="joined").count()
        left = await MemberEvent.filter(invite_link=link, event_type="left").count()
        pending = await JoinRequest.filter(invite_link=link, status="pending").count()
        declined = await JoinRequest.filter(invite_link=link, status="declined").count()
        current = joined - left

        total_joined += joined
        total_left += left
        total_pending += pending
        total_declined += declined

        if root:
            parts.append(
                f"\n🔗 Name: {link.name}\n"
                f"🔗 URL: <code>{link.url}</code>\n"
                f"⏳ Pending Requests: {pending}\n"
                f"🚫 Declined: {declined}\n"
                f"📥 Joined: {joined}\n"
                f"📤 Left: {left}\n"
                f"👤 Current: {current}"
            )
            delete_buttons.append(
                [InlineKeyboardButton(
                    text=f"🗑 Delete: {link.name}",
                    callback_data=f"del_link:{link.id}",
                )]
            )
        else:
            parts.append(
                f"\n🔗 Name: {link.name}\n"
                f"📥 Joined: {joined}"
            )

    total_current = total_joined - total_left

    if root:
        parts.append(
            f"\n───────────────\n"
            f"📈 <b>Overall Statistics:</b>\n"
            f"⏳ Total Pending: {total_pending}\n"
            f"🚫 Total Declined: {total_declined}\n"
            f"📥 Total Joins: {total_joined}\n"
            f"📤 Total Leaves: {total_left}\n"
            f"👤 Currently tracked: {total_current}"
        )
    else:
        parts.append(
            f"\n───────────────\n"
            f"📈 <b>Overall:</b>\n"
            f"📥 Total Joins: {total_joined}"
        )

    text = "\n".join(parts)
    buttons = delete_buttons + [
        [InlineKeyboardButton(text="🔄 Refresh", callback_data="stats")],
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=buttons)


async def cb_stats(callback: CallbackQuery, bot_config: dict):
    root = is_root_admin(callback.from_user.id, bot_config)
    text, markup = await build_stats(bot_config, root)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        pass
    await callback.answer()


async def msg_stats(message: Message, bot_config: dict):
    root = is_root_admin(message.from_user.id, bot_config)
    text, markup = await build_stats(bot_config, root)
    await message.answer(text, reply_markup=markup)


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

    # Refresh stats
    root = is_root_admin(callback.from_user.id, bot_config)
    text, markup = await build_stats(bot_config, root)
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        pass


def create_router() -> Router:
    router = Router()
    router.callback_query.register(cb_stats, F.data == "stats", IsAdmin())
    router.callback_query.register(cb_delete_link, F.data.startswith("del_link:"), IsRootAdmin())
    router.message.register(msg_stats, F.text == "📊 All Statistics", IsAdmin())
    return router
