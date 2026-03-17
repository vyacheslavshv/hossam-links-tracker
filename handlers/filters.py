from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from models import ClientAdmin


class IsAdmin(BaseFilter):
    """Passes for both root admins (from .env) and client admins (authenticated by password)."""

    async def __call__(self, event: Message | CallbackQuery, bot_config: dict) -> bool:
        user = event.from_user
        if not user:
            return False
        if user.id in bot_config.get("admin_ids", []):
            return True
        return await ClientAdmin.exists(bot_id=bot_config["bot_id"], user_id=user.id)


class IsRootAdmin(BaseFilter):
    """Passes only for root admins (from .env ADMIN_IDS)."""

    async def __call__(self, event: Message | CallbackQuery, bot_config: dict) -> bool:
        user = event.from_user
        if not user:
            return False
        return user.id in bot_config.get("admin_ids", [])


def is_root_admin(user_id: int, bot_config: dict) -> bool:
    return user_id in bot_config.get("admin_ids", [])
