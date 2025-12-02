import redis

from app.core.config import settings


class Cache:
    def __init__(self) -> None:
        self.__pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
        self.__client = redis.Redis(connection_pool=self.__pool)

    @property
    def redis(self) -> redis.Redis:
        return self.__client


cache = Cache()
