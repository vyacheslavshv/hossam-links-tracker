from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .filters import IsRootAdmin
from models import InviteLink


class LinkCreation(StatesGroup):
    waiting_name = State()


async def cb_create_link(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LinkCreation.waiting_name)
    await callback.message.edit_text(
        "🔗 <b>Create Invite Link</b>\n\n"
        "Send me the name for this link:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="menu")]
        ]),
    )
    await callback.answer()


async def msg_create_link(message: Message, state: FSMContext):
    await state.set_state(LinkCreation.waiting_name)
    await message.answer(
        "🔗 <b>Create Invite Link</b>\n\n"
        "Send me the name for this link:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="menu")]
        ]),
    )


async def process_link_name(message: Message, state: FSMContext, bot_config: dict):
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("❌ Name cannot be empty. Try again:")
        return

    bot: Bot = message.bot
    try:
        link = await bot.create_chat_invite_link(
            chat_id=bot_config["channel_id"],
            name=name,
            creates_join_request=True,
        )
    except Exception as e:
        await message.answer(f"❌ Failed to create link:\n<code>{e}</code>")
        await state.clear()
        return

    await InviteLink.create(
        bot_id=bot_config["bot_id"],
        name=name,
        url=link.invite_link,
    )

    await state.clear()
    await message.answer(
        f"✅ <b>Link Created!</b>\n\n"
        f"🔗 Name: {name}\n"
        f"URL: <code>{link.invite_link}</code>\n\n"
        f"Share this link to invite members.",
    )


def create_router() -> Router:
    router = Router()
    router.callback_query.register(cb_create_link, F.data == "create_link", IsRootAdmin())
    router.message.register(msg_create_link, F.text == "🔗 Create Tracking Link", IsRootAdmin())
    router.message.register(process_link_name, LinkCreation.waiting_name, IsRootAdmin())
    return router
