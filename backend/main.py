# Safina API - Version 1.1.0 (Enhanced Stability & Resilience)
import asyncio
import os
import contextlib
from typing import AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

from app.core.logging_config import setup_logging, get_logger
from app.core.logging_middleware import LoggingMiddleware
from app.core.database import engine, Base
from app.api import auth, projects, expenses, team, notifications, analytics
from app.db import models, schemas, seed
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing application lifespan...")
    
    # 2. Seed initial data (e.g., Senior Financier)
    seed.seed_users()

    # 3. Start Telegram Bot task in the background
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
    "http://localhost:8000",
]

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPExtensions with a consistent JSON format."""
    logger.error(f"HTTP Error: {exc.status_code} - {exc.detail} | Path: {request.url.path}")
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "path": request.url.path
        },
    )
    # Permissive CORS for troubleshooting - returning * is safest for 'removing cross-origin'
    response.headers["Access-Control-Allow-Origin"] = "*"
    # Credentials must be false if origin is *
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for any unexpected application errors."""
    logger.critical(f"Uncaught Exception: {str(exc)} | Path: {request.url.path}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={
            "status": "critical_error",
            "message": "An unexpected error occurred internal to the server.",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else "Contact administrator"
        },
    )
    # Permissive CORS for troubleshooting
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Add structured logging middleware
app.add_middleware(LoggingMiddleware)

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
app.include_router(notifications.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

@app.get("/ping")
async def ping():
    return "pong"

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok", 
        "version": "1.1.4", 
        "database": "connected",
        "cors": "permissive"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
