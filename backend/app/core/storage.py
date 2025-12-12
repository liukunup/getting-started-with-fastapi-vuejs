import io
import logging
import uuid
from datetime import timedelta
from urllib.parse import urlparse

from minio import Minio

from app.core.config import settings

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self) -> None:
        self.__bucket_name = settings.STORAGE_BUCKET_NAME
        self.__client = Minio(
            endpoint=settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY,
            secure=settings.STORAGE_SECURE,
        )
        # Ensure bucket exists
        try:
            self._ensure_bucket()
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")

    @property
    def minio(self) -> Minio:
        return self.__client

    def _ensure_bucket(self) -> None:
        """Ensure the default bucket exists."""
        if not self.__client.bucket_exists(bucket_name=self.__bucket_name):
            self.__client.make_bucket(bucket_name=self.__bucket_name)
            logger.info(f"Created bucket: {self.__bucket_name}")

    def get_presigned_url(
        self,
        object_name: str,
        method: str = "GET",
        expires: timedelta = timedelta(minutes=15),
    ) -> str:
        """Generate a presigned URL for the object."""
        url = self.__client.get_presigned_url(
            method,
            self.__bucket_name,
            object_name,
            expires=expires,
        )
        # Convert to frontend S3 proxy URL
        parsed = urlparse(url)
        return f"{settings.FRONTEND_HOST}/s3{parsed.path}?{parsed.query}"

    def save_avatar(self, user_id: uuid.UUID, data: bytes, content_type: str) -> str:
        """Upload user avatar to the storage and return its object name."""
        # Generate unique filename
        ext = content_type.split("/")[-1]
        if ext == "jpeg":
            ext = "jpg"
        filename = f"{uuid.uuid4()}.{ext}"

        # Define object name (private path)
        object_name = f"avatars/{user_id}/{filename}"

        # Upload the object
        self.__client.put_object(
            bucket_name=self.__bucket_name,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info(f"Uploaded avatar for user {user_id} to {object_name}")
        return object_name


storage = Storage()
