import asyncio
import logging
from typing import Final
import redis.asyncio as redis

from question_parsing import LOGGER_NAME


class RedisCache:
    USER_YOUTUBE_CACHE_PREFIX: Final[str] = r"user-recommendation-cache-youtube-{name}"
    USER_LEETCODE_CACHE_PREFIX: Final[str] = r"user-recommendation-cache-lc-{name}"

    def __init__(self, redis_ip: str, redis_port: int):
        self._log = logging.getLogger(LOGGER_NAME)
        self._redis_client = redis.from_url(f"redis://{redis_ip}:{redis_port}")
        self._lock = asyncio.Lock()

    async def invalidate_user(self, user: str):
        keys = [RedisCache.USER_YOUTUBE_CACHE_PREFIX.format(name=user),
                RedisCache.USER_LEETCODE_CACHE_PREFIX.format(name=user)]
        async with self._lock:
            self._log.info(f"expired cache for user: {user}")
            for key in keys:
                if await self._redis_client.exists(key):
                    await self._redis_client.expire(key, 0)
