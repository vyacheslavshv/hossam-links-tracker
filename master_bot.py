"""Master bot for dynamically adding/removing worker bots."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from bot_manager import BotManager
from config import ADMIN_IDS
from models import BotConfig


class AddBot(StatesGroup):
    token = State()
    channel_id = State()
    notification_channel_id = State()


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def create_master_router(manager: BotManager) -> Router:
    router = Router()

    # ── Main menu ────────────────────────────────────────────

    async def _send_main_menu(target, manager: BotManager):
        """Send main menu. target is Message or CallbackQuery."""
        running = manager.running_bots
        lines = ["<b>🤖 Bot Manager</b>\n"]
        if running:
            lines.append(f"Running bots: <b>{len(running)}</b>\n")
            for cfg in running.values():
                lines.append(
                    f"  • @{cfg.get('bot_username', '?')} → "
                    f"{cfg.get('channel_title', 'Unknown')}"
                )
        else:
            lines.append("No bots running.")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add Bot", callback_data="master:add")],
            [InlineKeyboardButton(text="🗑 Remove Bot", callback_data="master:remove_list")],
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="master:refresh")],
        ])

        text = "\n".join(lines)

        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=keyboard)
        else:
            await target.answer(text, reply_markup=keyboard)

    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        if not _is_admin(message.from_user.id):
            return
        await state.clear()
        await _send_main_menu(message, manager)

    @router.callback_query(F.data == "master:refresh")
    async def cb_refresh(callback: CallbackQuery, state: FSMContext):
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔️", show_alert=True)
        await state.clear()
        await _send_main_menu(callback, manager)
        await callback.answer()

    # ── Add bot flow ─────────────────────────────────────────

    @router.callback_query(F.data == "master:add")
    async def cb_add_start(callback: CallbackQuery, state: FSMContext):
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔️", show_alert=True)
        await state.set_state(AddBot.token)
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="master:cancel")],
        ])
        await callback.message.edit_text(
            "Send me the <b>bot token</b>:",
            reply_markup=cancel_kb,
        )
        await callback.answer()

    @router.message(AddBot.token)
    async def on_token(message: Message, state: FSMContext):
        if not _is_admin(message.from_user.id):
            return
        token = message.text.strip()
        if ":" not in token:
            await message.answer("❌ Invalid token format. Try again:")
            return
        await state.update_data(token=token)
        await state.set_state(AddBot.channel_id)
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="master:cancel")],
        ])
        await message.answer(
            "Now send the <b>channel ID</b> (negative number):",
            reply_markup=cancel_kb,
        )

    @router.message(AddBot.channel_id)
    async def on_channel_id(message: Message, state: FSMContext):
        if not _is_admin(message.from_user.id):
            return
        try:
            channel_id = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Must be a number. Try again:")
            return
        await state.update_data(channel_id=channel_id)
        await state.set_state(AddBot.notification_channel_id)
        skip_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip (same as channel)", callback_data="master:skip_notif")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="master:cancel")],
        ])
        await message.answer(
            "Send the <b>notification channel ID</b>, or skip to use the same channel:",
            reply_markup=skip_kb,
        )

    @router.callback_query(F.data == "master:skip_notif", AddBot.notification_channel_id)
    async def cb_skip_notif(callback: CallbackQuery, state: FSMContext):
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔️", show_alert=True)
        data = await state.get_data()
        await state.clear()
        await callback.message.edit_text("⏳ Starting bot...")
        await callback.answer()
        await _finish_add_bot(callback.message, manager, data["token"], data["channel_id"], None)

    @router.message(AddBot.notification_channel_id)
    async def on_notification_channel_id(message: Message, state: FSMContext):
        if not _is_admin(message.from_user.id):
            return
        try:
            notif_id = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Must be a number. Try again:")
            return
        data = await state.get_data()
        await state.clear()
        await message.answer("⏳ Starting bot...")
        await _finish_add_bot(message, manager, data["token"], data["channel_id"], notif_id)

    async def _finish_add_bot(message: Message, manager: BotManager,
                              token: str, channel_id: int,
                              notification_channel_id: int | None):
        try:
            bot_config = await manager.start_bot(
                bot_token=token,
                channel_id=channel_id,
                notification_channel_id=notification_channel_id,
            )
        except Exception as e:
            await message.answer(f"❌ Failed to start bot:\n<code>{e}</code>")
            return

        # Save to DB
        await BotConfig.update_or_create(
            bot_token=token,
            defaults={
                "channel_id": channel_id,
                "notification_channel_id": notification_channel_id,
                "is_active": True,
            },
        )

        await message.answer(
            f"✅ Bot <b>@{bot_config['bot_username']}</b> started!\n"
            f"Channel: {bot_config.get('channel_title', 'Unknown')}"
        )

    # ── Remove bot flow ──────────────────────────────────────

    @router.callback_query(F.data == "master:remove_list")
    async def cb_remove_list(callback: CallbackQuery):
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔️", show_alert=True)

        running = manager.running_bots
        if not running:
            await callback.answer("No bots running", show_alert=True)
            return

        buttons = []
        for bot_id, cfg in running.items():
            label = f"@{cfg.get('bot_username', '?')} — {cfg.get('channel_title', '?')}"
            buttons.append([InlineKeyboardButton(
                text=f"🗑 {label}",
                callback_data=f"master:remove:{bot_id}",
            )])
        buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="master:refresh")])

        await callback.message.edit_text(
            "Select a bot to remove:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("master:remove:"))
    async def cb_remove_confirm(callback: CallbackQuery):
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔️", show_alert=True)

        bot_id = int(callback.data.split(":")[2])
        cfg = manager.running_bots.get(bot_id)
        if not cfg:
            await callback.answer("Bot not found", show_alert=True)
            return

        username = cfg.get("bot_username", "?")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes, remove", callback_data=f"master:remove_yes:{bot_id}"),
                InlineKeyboardButton(text="❌ No", callback_data="master:remove_list"),
            ],
        ])
        await callback.message.edit_text(
            f"Are you sure you want to remove <b>@{username}</b>?",
            reply_markup=keyboard,
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("master:remove_yes:"))
    async def cb_remove_yes(callback: CallbackQuery):
        if not _is_admin(callback.from_user.id):
            return await callback.answer("⛔️", show_alert=True)

        bot_id = int(callback.data.split(":")[2])
        cfg = manager.running_bots.get(bot_id)
        username = cfg.get("bot_username", "?") if cfg else "?"
        token = cfg.get("bot_token") if cfg else None

        stopped = await manager.stop_bot(bot_id)

        if token:
            await BotConfig.filter(bot_token=token).update(is_active=False)

        if stopped:
            await callback.message.edit_text(f"✅ Bot <b>@{username}</b> removed and stopped.")
        else:
            await callback.message.edit_text("⚠️ Bot was not running.")
        await callback.answer()

    # ── Cancel ───────────────────────────────────────────────

    @router.callback_query(F.data == "master:cancel")
    async def cb_cancel(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await _send_main_menu(callback, manager)
        await callback.answer("Cancelled")

    return router


async def run_master_bot(token: str, manager: BotManager):
    """Start the master bot polling loop."""
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    me = await bot.get_me()
    logger.info(f"Master bot @{me.username} started")

    dp = Dispatcher()
    dp.include_router(create_master_router(manager))

    try:
        await dp.start_polling(
            bot,
            handle_signals=False,
            allowed_updates=["message", "callback_query"],
        )
    finally:
        await bot.session.close()
