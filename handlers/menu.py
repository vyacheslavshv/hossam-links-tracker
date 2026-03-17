from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from .filters import IsAdmin

router = Router()


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 All Statistics", callback_data="stats")],
        [InlineKeyboardButton(text="🔗 Create Tracking Link", callback_data="create_link")],
        [InlineKeyboardButton(text="📋 All Links", callback_data="links_list")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")],
    ])


@router.message(CommandStart(), IsAdmin())
async def cmd_start(message: Message, state: FSMContext, bot_config: dict):
    await state.clear()
    channel = bot_config.get("channel_title", "Unknown")
    await message.answer(
        f"🏠 <b>Main Menu</b>\n\n"
        f"📢 Channel: <b>{channel}</b>\n\n"
        f"Select an option:",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "menu", IsAdmin())
async def cb_menu(callback: CallbackQuery, state: FSMContext, bot_config: dict):
    await state.clear()
    channel = bot_config.get("channel_title", "Unknown")
    await callback.message.edit_text(
        f"🏠 <b>Main Menu</b>\n\n"
        f"📢 Channel: <b>{channel}</b>\n\n"
        f"Select an option:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "open_menu", IsAdmin())
async def cb_open_menu(callback: CallbackQuery, state: FSMContext, bot_config: dict):
    """Opens menu as a NEW message (so the notification/report stays visible)."""
    await state.clear()
    channel = bot_config.get("channel_title", "Unknown")
    await callback.message.answer(
        f"🏠 <b>Main Menu</b>\n\n"
        f"📢 Channel: <b>{channel}</b>\n\n"
        f"Select an option:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
