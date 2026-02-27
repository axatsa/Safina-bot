# Safina API - Version 1.0.1 (Fixed CORS and Bot Integration)
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.logging_config import setup_logging, get_logger
from app.core.logging_middleware import LoggingMiddleware

# Setup logging
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Telegram Bot
    if os.getenv("BOT_TOKEN"):
        logger.info("Starting Telegram Bot task...")
        asyncio.create_task(bot_main())
    else:
        logger.warning("BOT_TOKEN not found in environment. Bot will not be started.")
    yield
    # Shutdown
    logger.info("Shutting down API...")

# Create tables
models.Base.metadata.create_all(bind=engine)

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
