# Safina API - Version 1.1.0 (Enhanced Stability & Resilience)
import asyncio
import os
import contextlib
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

from app.core.logging_config import setup_logging, get_logger
from app.core.logging_middleware import LoggingMiddleware
from app.core.database import engine, Base
from app.api import auth, projects, expenses, team
from app.services.bot.main import main as bot_main

# Setup logging
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

async def init_db_with_retry(max_retries: int = 5, delay: int = 5):
    """Attempt to create database tables with retries."""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"DB initialized attempt {attempt}/{max_retries}...")
            # Metadata.create_all is synchronous, run it in a thread if needed, 
            # but for startup it's fine to block for a bit
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created successfully.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed (attempt {attempt}): {str(e)}")
            if attempt < max_retries:
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.critical("Could not connect to database after max retries. Application will likely fail.")
                return False
        except Exception as e:
            logger.error(f"Unexpected error during DB init: {str(e)}", exc_info=True)
            return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing application lifespan...")
    
    # 1. Initialize DB
    await init_db_with_retry()

    # 2. Start Telegram Bot task in the background
    bot_task = None
    if os.getenv("BOT_TOKEN"):
        bot_task = asyncio.create_task(run_bot_with_watchdog())
    else:
        logger.warning("BOT_TOKEN not found in environment. Bot will not be started.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if bot_task:
        logger.info("Cancelling bot task...")
        bot_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await bot_task

app = FastAPI(title="Safina API", lifespan=lifespan)

# Add structured logging middleware
app.add_middleware(LoggingMiddleware)

# Allowed origins
origins = [
    "https://finance.thompson.uz",
    "https://api-finance.thompson.uz",
    "http://finance.thompson.uz",
    "http://api-finance.thompson.uz",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(team.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
