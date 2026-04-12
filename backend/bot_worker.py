import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

from app.core.logging_config import setup_logging, get_logger
from app.services.bot.main import main as bot_main
from app.core.database import engine, Base

setup_logging()
logger = get_logger(__name__)

async def run_bot_with_watchdog():
    """Run the bot in a loop, restarting it if it crashes."""
    retry_delay = 5  # Start with 5 seconds
    while True:
        try:
            logger.info("Starting Telegram Bot task...")
            await bot_main()
            logger.warning("Bot main task finished unexpectedly without error.")
        except Exception as e:
            logger.error(f"Bot crashed with error: {str(e)}", exc_info=True)
        
        logger.info(f"Restarting bot in {retry_delay} seconds...")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60) # Exponential backoff up to 1 min

if __name__ == "__main__":
    logger.info("Initializing Safina Telegram Bot Worker...")
    if not os.getenv("BOT_TOKEN"):
        logger.error("BOT_TOKEN not found in environment. Exiting.")
        exit(1)
        
    try:
        asyncio.run(run_bot_with_watchdog())
    except KeyboardInterrupt:
        logger.info("Bot worker stopped by user.")
