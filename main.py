import asyncio
import signal

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from config import load_bots_config
from utils import setup_logging, init_db, close_db
from handlers import create_router
from scheduler import scheduler_loop


async def run_bot(bot_config: dict):
    bot = Bot(
        token=bot_config["bot_token"],
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    me = await bot.get_me()
    bot_config["bot_id"] = me.id
    bot_config["bot_username"] = me.username

    try:
        chat = await bot.get_chat(bot_config["channel_id"])
        bot_config["channel_title"] = chat.title
        bot_config["channel_username"] = chat.username
    except Exception as e:
        logger.warning(f"[@{me.username}] Could not fetch channel info: {e}")
        bot_config["channel_title"] = "Unknown"
        bot_config["channel_username"] = None

    dp = Dispatcher()
    dp["bot_config"] = bot_config
    dp.include_router(create_router())

    logger.info(
        f"Bot @{me.username} (ID: {me.id}) started "
        f"for channel \"{bot_config.get('channel_title', 'Unknown')}\""
    )

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


async def main():
    setup_logging()
    await init_db()

    bots_config = load_bots_config()

    if not bots_config:
        logger.error("No bots configured in bots.json")
        return

    logger.info(f"Starting {len(bots_config)} bot(s)...")

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def handle_signal():
        if not shutdown_event.is_set():
            logger.info("Shutdown signal received, stopping bots...")
            shutdown_event.set()

    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    tasks = [asyncio.create_task(run_bot(cfg)) for cfg in bots_config]

    await shutdown_event.wait()

    for task in tasks:
        task.cancel()

    try:
        await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=10,
        )
    except asyncio.TimeoutError:
        logger.warning("Shutdown timed out after 10s, forcing exit")

    await close_db()
    logger.info("All bots stopped")


if __name__ == "__main__":
    asyncio.run(main())
