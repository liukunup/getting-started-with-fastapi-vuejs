from minio import Minio

from app.core.config import settings


class Storage:
    def __init__(self) -> None:
        self.__client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

    @property
    def minio(self) -> Minio:
        return self.__client


storage = Storage()
