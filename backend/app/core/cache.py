import redis

from app.core.config import settings


class Cache:
    def __init__(self) -> None:
        self.pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB_INDEX,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        self.client = redis.Redis(connection_pool=self.pool)


redis_client = Cache().client
