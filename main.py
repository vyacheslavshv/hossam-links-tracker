import asyncio
import signal

from loguru import logger

from config import MASTER_BOT_TOKEN
from utils import setup_logging, init_db, close_db
from bot_manager import BotManager
from master_bot import run_master_bot
from models import BotConfig


async def main():
    setup_logging()
    await init_db()

    if not MASTER_BOT_TOKEN:
        logger.error("MASTER_BOT_TOKEN is not set in .env")
        return

    manager = BotManager()

    # Load saved bots from DB and start them
    saved_bots = await BotConfig.filter(is_active=True).all()
    for bot_cfg in saved_bots:
        try:
            await manager.start_bot(
                bot_token=bot_cfg.bot_token,
                channel_id=bot_cfg.channel_id,
                notification_channel_id=bot_cfg.notification_channel_id,
                timezone=bot_cfg.timezone,
            )
        except Exception as e:
            logger.error(f"Failed to start saved bot (token=...{bot_cfg.bot_token[-6:]}): {e}")

    logger.info(f"Loaded {len(manager.running_bots)} bot(s) from database")

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def handle_signal():
        if not shutdown_event.is_set():
            logger.info("Shutdown signal received, stopping...")
            shutdown_event.set()

    loop.add_signal_handler(signal.SIGINT, handle_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_signal)

    master_task = asyncio.create_task(run_master_bot(MASTER_BOT_TOKEN, manager))

    await shutdown_event.wait()

    master_task.cancel()
    try:
        await master_task
    except asyncio.CancelledError:
        pass

    await manager.stop_all()
    await close_db()
    logger.info("All bots stopped")


if __name__ == "__main__":
    asyncio.run(main())
