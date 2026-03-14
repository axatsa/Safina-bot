import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from .handlers import register_all_handlers as register_handlers
from dotenv import load_dotenv

load_dotenv()

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis = Redis.from_url(redis_url)
            storage = RedisStorage(redis=redis)
            print(f"Using RedisStorage at {redis_url}")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}. Falling back to MemoryStorage.")
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()
        print("Using MemoryStorage (REDIS_URL not set)")
        
    dp = Dispatcher(storage=storage)
    
    register_handlers(dp)
    
    print("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
