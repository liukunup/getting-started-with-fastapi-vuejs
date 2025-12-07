import json
import logging
import uuid
from typing import BinaryIO

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
        self.__protocol = "https" if settings.STORAGE_SECURE else "http"
        self.__url_prefix = (
            f"{self.__protocol}://{settings.STORAGE_ENDPOINT}/{self.__bucket_name}"
        )

        # Ensure bucket exists
        try:
            self._ensure_bucket()
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")

        # Ensure policy is set even if bucket already exists
        try:
            self._set_public_read_policy()
        except Exception as e:
            logger.warning(f"Failed to set public read policy: {e}")

    @property
    def minio(self) -> Minio:
        return self.__client

    def _ensure_bucket(self) -> None:
        """Ensure the default bucket exists."""
        if not self.__client.bucket_exists(bucket_name=self.__bucket_name):
            self.__client.make_bucket(bucket_name=self.__bucket_name)
            logger.info(f"Created bucket: {self.__bucket_name}")

    def _set_public_read_policy(self) -> None:
        """Set bucket policy to allow public read access."""
        # Policy to allow anonymous read access
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.__bucket_name}/public/*"],
                }
            ],
        }
        # Set the bucket policy to allow public read access
        self.__client.set_bucket_policy(self.__bucket_name, json.dumps(policy))
        logger.info(
            f"Set public read policy for bucket: {self.__bucket_name}, path: public/*"
        )

    def upload_avatar(
        self, user_id: uuid.UUID, filename: str, data: BinaryIO, content_type: str
    ) -> str:
        """Upload user avatar to the storage and return its public URL."""
        # Define object name
        object_name = f"public/avatars/{user_id}/{filename}"
        # Calculate length
        data.seek(0, 2)
        length = data.tell()
        data.seek(0)
        # Upload the object
        self.__client.put_object(
            bucket_name=self.__bucket_name,
            object_name=object_name,
            data=data,
            length=length,
            content_type=content_type,
        )
        url = f"{self.__url_prefix}/{object_name}"
        logger.info(f"Uploaded avatar for user {user_id} to {url}")
        return url


storage = Storage()
