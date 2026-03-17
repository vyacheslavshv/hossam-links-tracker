from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, bot_config: dict) -> bool:
        user = event.from_user
        if not user:
            return False
        return user.id in bot_config.get("admin_ids", [])
