from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from .filters import IsAdmin
from models import InviteLink, MemberEvent, JoinRequest

router = Router()


class LinkCreation(StatesGroup):
    waiting_name = State()


@router.callback_query(F.data == "create_link", IsAdmin())
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


@router.message(LinkCreation.waiting_name, IsAdmin())
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
        await message.answer(
            f"❌ Failed to create link:\n<code>{e}</code>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
            ]),
        )
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
        f"🔗 URL: <code>{link.invite_link}</code>\n\n"
        f"Share this link to invite members.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistics", callback_data="stats")],
            [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
        ]),
    )


@router.callback_query(F.data == "links_list", IsAdmin())
async def cb_links_list(callback: CallbackQuery, bot_config: dict):
    links = await InviteLink.filter(bot_id=bot_config["bot_id"], revoked=False).order_by("-created_at")

    if not links:
        await callback.message.edit_text(
            "📋 <b>Links</b>\n\nNo active links found.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Create Link", callback_data="create_link")],
                [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
            ]),
        )
        await callback.answer()
        return

    buttons = []
    for link in links:
        joined = await MemberEvent.filter(invite_link=link, event_type="joined").count()
        left = await MemberEvent.filter(invite_link=link, event_type="left").count()
        current = joined - left
        buttons.append([InlineKeyboardButton(
            text=f"🔗 {link.name} — 👤 {current}",
            callback_data=f"link:{link.id}",
        )])
    buttons.append([InlineKeyboardButton(text="🔗 Create Link", callback_data="create_link")])
    buttons.append([InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")])

    await callback.message.edit_text(
        "📋 <b>All Links</b>\n\nSelect a link to manage:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("link:"), IsAdmin())
async def cb_link_detail(callback: CallbackQuery, bot_config: dict):
    link_id = int(callback.data.split(":")[1])
    link = await InviteLink.get_or_none(id=link_id, bot_id=bot_config["bot_id"])

    if not link:
        await callback.answer("❌ Link not found", show_alert=True)
        return

    joined = await MemberEvent.filter(invite_link=link, event_type="joined").count()
    left = await MemberEvent.filter(invite_link=link, event_type="left").count()
    pending = await JoinRequest.filter(invite_link=link, status="pending").count()
    declined = await JoinRequest.filter(invite_link=link, status="declined").count()
    current = joined - left

    text = (
        f"📊 <b>Tracking Statistics</b>\n\n"
        f"🔗 Name: {link.name}\n"
        f"🔗 URL: <code>{link.url}</code>\n"
        f"⏳ Pending Requests: {pending}\n"
        f"🚫 Declined: {declined}\n"
        f"📥 Joined: {joined}\n"
        f"📤 Left: {left}\n"
        f"👤 Current: {current}"
    )

    buttons = [
        [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"link:{link.id}")],
        [InlineKeyboardButton(text="🗑 Revoke Link", callback_data=f"revoke:{link.id}")],
        [InlineKeyboardButton(text="🔙 All Links", callback_data="links_list")],
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("revoke:"), IsAdmin())
async def cb_revoke_link(callback: CallbackQuery, bot_config: dict):
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
    except Exception:
        pass

    link.revoked = True
    await link.save()

    await callback.message.edit_text(
        f"✅ Link <b>{link.name}</b> has been revoked.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 All Links", callback_data="links_list")],
            [InlineKeyboardButton(text="🔙 Main Menu", callback_data="menu")],
        ]),
    )
    await callback.answer()
