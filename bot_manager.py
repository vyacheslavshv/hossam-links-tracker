import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from handlers import create_router
from scheduler import scheduler_loop
from config import ADMIN_IDS, TIMEZONE


class BotManager:
    """Manages dynamic start/stop of worker bots."""

    def __init__(self):
        self._tasks: dict[int, asyncio.Task] = {}  # bot_id -> task
        self._bots: dict[int, Bot] = {}  # bot_id -> Bot instance
        self._configs: dict[int, dict] = {}  # bot_id -> bot_config dict

    @property
    def running_bots(self) -> dict[int, dict]:
        return dict(self._configs)

    async def start_bot(self, bot_token: str, channel_id: int,
                        notification_channel_id: int | None = None,
                        timezone: str | None = None) -> dict:
        """Start a worker bot. Returns bot_config dict with bot_id, bot_username, etc."""
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

        me = await bot.get_me()
        bot_id = me.id

        if bot_id in self._tasks and not self._tasks[bot_id].done():
            await bot.session.close()
            raise ValueError(f"Bot @{me.username} is already running")

        bot_config = {
            "bot_token": bot_token,
            "channel_id": channel_id,
            "notification_channel_id": notification_channel_id,
            "admin_ids": list(ADMIN_IDS),
            "timezone": timezone or TIMEZONE,
            "bot_id": bot_id,
            "bot_username": me.username,
        }

        try:
            chat = await bot.get_chat(channel_id)
            bot_config["channel_title"] = chat.title
            bot_config["channel_username"] = chat.username
        except Exception as e:
            logger.warning(f"[@{me.username}] Could not fetch channel info: {e}")
            bot_config["channel_title"] = "Unknown"
            bot_config["channel_username"] = None

        task = asyncio.create_task(self._run_bot(bot, bot_config))
        self._tasks[bot_id] = task
        self._bots[bot_id] = bot
        self._configs[bot_id] = bot_config

        logger.info(
            f"Bot @{me.username} (ID: {bot_id}) started "
            f"for channel \"{bot_config.get('channel_title', 'Unknown')}\""
        )

        return bot_config

    async def stop_bot(self, bot_id: int) -> bool:
        """Stop a running bot by its bot_id. Returns True if stopped."""
        task = self._tasks.pop(bot_id, None)
        if task is None:
            return False

        task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=5)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        self._bots.pop(bot_id, None)
        config = self._configs.pop(bot_id, None)
        username = config.get("bot_username", "?") if config else "?"
        logger.info(f"Bot @{username} (ID: {bot_id}) stopped")
        return True

    async def stop_all(self):
        bot_ids = list(self._tasks.keys())
        for bot_id in bot_ids:
            await self.stop_bot(bot_id)

    @staticmethod
    async def _run_bot(bot: Bot, bot_config: dict):
        dp = Dispatcher()
        dp["bot_config"] = bot_config
        dp.include_router(create_router())

        scheduler_task = asyncio.create_task(scheduler_loop(bot, bot_config))

        try:
            await dp.start_polling(
                bot,
                handle_signals=False,
                allowed_updates=[
                    "message",
                    "callback_query",
                    "chat_join_request",
                    "chat_member",
                    "my_chat_member",
                ],
            )
        finally:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass
            await bot.session.close()
