from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
)

from config import BOT_PASSWORD
from models import ClientAdmin
from .filters import IsAdmin, is_root_admin


class Auth(StatesGroup):
    waiting_password = State()


async def refresh_channel_info(bot: Bot, bot_config: dict):
    try:
        chat = await bot.get_chat(bot_config["channel_id"])
        bot_config["channel_title"] = chat.title
        bot_config["channel_username"] = chat.username
    except Exception:
        pass


def reply_kb(root: bool = True) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📊 All Statistics")],
    ]
    if root:
        buttons.append([KeyboardButton(text="🔗 Create Tracking Link")])
    if root:
        buttons.append([KeyboardButton(text="⚙️ Settings")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def menu_text(bot_config: dict) -> str:
    channel = bot_config.get("channel_title", "Unknown")
    return (
        f"🏠 <b>Main Menu</b>\n\n"
        f"📢 Channel: <b>{channel}</b>\n\n"
        f"Select an option:"
    )


# ── /start for admins ──

async def cmd_start(message: Message, state: FSMContext, bot_config: dict):
    await state.clear()
    await refresh_channel_info(message.bot, bot_config)
    root = is_root_admin(message.from_user.id, bot_config)
    await message.answer(menu_text(bot_config), reply_markup=reply_kb(root))


# ── /start for unknown users → ask password ──

async def cmd_start_auth(message: Message, state: FSMContext):
    await state.set_state(Auth.waiting_password)
    await message.answer("🔐 Enter the access password:")


async def process_password(message: Message, state: FSMContext, bot_config: dict):
    if message.text and message.text.strip() == BOT_PASSWORD:
        await ClientAdmin.get_or_create(
            bot_id=bot_config["bot_id"],
            user_id=message.from_user.id,
        )
        await state.clear()
        await message.answer(
            "✅ Access granted!\n\n" + menu_text(bot_config),
            reply_markup=reply_kb(root=False),
        )
    else:
        await message.answer("❌ Wrong password. Try again:")


# ── Menu callback (for legacy inline buttons) ──

async def cb_menu(callback: CallbackQuery, state: FSMContext, bot_config: dict):
    await state.clear()
    await refresh_channel_info(callback.bot, bot_config)
    root = is_root_admin(callback.from_user.id, bot_config)
    await callback.message.answer(menu_text(bot_config), reply_markup=reply_kb(root))
    await callback.answer()


def create_router() -> Router:
    router = Router()
    router.message.register(cmd_start, CommandStart(), IsAdmin())
    router.message.register(cmd_start_auth, CommandStart())
    router.message.register(process_password, Auth.waiting_password)
    router.callback_query.register(cb_menu, F.data == "menu", IsAdmin())
    return router
