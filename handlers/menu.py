from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_PASSWORD
from models import ClientAdmin
from .filters import IsAdmin, is_root_admin

router = Router()


class Auth(StatesGroup):
    waiting_password = State()


def main_menu_kb(root: bool = True) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📊 All Statistics", callback_data="stats")],
    ]
    if root:
        buttons.append([InlineKeyboardButton(text="🔗 Create Tracking Link", callback_data="create_link")])
    buttons.append([InlineKeyboardButton(text="📋 All Links", callback_data="links_list")])
    if root:
        buttons.append([InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def menu_text(bot_config: dict) -> str:
    channel = bot_config.get("channel_title", "Unknown")
    return (
        f"🏠 <b>Main Menu</b>\n\n"
        f"📢 Channel: <b>{channel}</b>\n\n"
        f"Select an option:"
    )


# ── /start for admins ──

@router.message(CommandStart(), IsAdmin())
async def cmd_start(message: Message, state: FSMContext, bot_config: dict):
    await state.clear()
    root = is_root_admin(message.from_user.id, bot_config)
    await message.answer(menu_text(bot_config), reply_markup=main_menu_kb(root))


# ── /start for unknown users → ask password ──

@router.message(CommandStart())
async def cmd_start_auth(message: Message, state: FSMContext):
    await state.set_state(Auth.waiting_password)
    await message.answer("🔐 Enter the access password:")


@router.message(Auth.waiting_password)
async def process_password(message: Message, state: FSMContext, bot_config: dict):
    if message.text and message.text.strip() == BOT_PASSWORD:
        await ClientAdmin.get_or_create(
            bot_id=bot_config["bot_id"],
            user_id=message.from_user.id,
        )
        await state.clear()
        await message.answer(
            "✅ Access granted!\n\n" + menu_text(bot_config),
            reply_markup=main_menu_kb(root=False),
        )
    else:
        await message.answer("❌ Wrong password. Try again:")


# ── Menu callbacks ──

@router.callback_query(F.data == "menu", IsAdmin())
async def cb_menu(callback: CallbackQuery, state: FSMContext, bot_config: dict):
    await state.clear()
    root = is_root_admin(callback.from_user.id, bot_config)
    await callback.message.edit_text(menu_text(bot_config), reply_markup=main_menu_kb(root))
    await callback.answer()


@router.callback_query(F.data == "open_menu", IsAdmin())
async def cb_open_menu(callback: CallbackQuery, state: FSMContext, bot_config: dict):
    """Opens menu as a NEW message (so the notification/report stays visible)."""
    await state.clear()
    root = is_root_admin(callback.from_user.id, bot_config)
    await callback.message.answer(menu_text(bot_config), reply_markup=main_menu_kb(root))
    await callback.answer()
