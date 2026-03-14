import httpx
import asyncio
from datetime import datetime, timedelta
import redis.asyncio as redis
import os
import json
from decimal import Decimal
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class CurrencyService:
    API_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"
    CACHE_KEY = "currency_rates_cbu"
    CACHE_TTL = 3600  # 1 hour

    def __init__(self):
        redis_url = os.getenv("REDIS_URL")
        self.redis = redis.from_url(redis_url) if redis_url else None

    async def get_usd_rate(self) -> float:
        """Get current USD to UZS rate from CBU."""
        if self.redis:
            cached = await self.redis.get(self.CACHE_KEY)
            if cached:
                try:
                    rates = json.loads(cached)
                    for rate in rates:
                        if rate.get("Ccy") == "USD":
                            return Decimal(rate.get("Rate"))
                except (json.JSONDecodeError, ValueError):
                    logger.error("Failed to parse cached rates")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.API_URL, timeout=10.0)
                response.raise_for_status()
                rates = response.json()
                
                if self.redis:
                    await self.redis.setex(self.CACHE_KEY, self.CACHE_TTL, json.dumps(rates))
                
                for rate in rates:
                    if rate.get("Ccy") == "USD":
                        return Decimal(rate.get("Rate"))
        except Exception as e:
            logger.error(f"Error fetching rates from CBU: {e}")
            # Fallback to a reasonable default or last known good rate if needed
            fallback = os.getenv("USD_FALLBACK_RATE", "12500.0")
            return Decimal(fallback)

        fallback = os.getenv("USD_FALLBACK_RATE", "12500.0")
        return Decimal(fallback)

currency_service = CurrencyService()
