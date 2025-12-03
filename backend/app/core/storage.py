from io import BytesIO
import logging
from minio import Minio

from app.core.config import settings

logger = logging.getLogger(__name__)


class Storage:
    def __init__(self) -> None:
        self.__client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        # Ensure bucket exists
        try:
            self._ensure_bucket()
        except Exception as e:
            logger.warning(f"Failed to ensure bucket exists: {e}")

    @property
    def minio(self) -> Minio:
        return self.__client

    def _ensure_bucket(self) -> None:
        """Ensure the default bucket exists with public read policy."""
        bucket_name = settings.MINIO_BUCKET_NAME
        if not self.__client.bucket_exists(bucket_name):
            self.__client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")
            # Set public read policy for the bucket
            self._set_public_read_policy(bucket_name)
        else:
            # Ensure policy is set even if bucket already exists
            try:
                self._set_public_read_policy(bucket_name)
            except Exception as e:
                logger.warning(f"Failed to set public read policy: {e}")
    
    def _set_public_read_policy(self, bucket_name: str) -> None:
        """Set bucket policy to allow public read access."""
        import json
        
        # Policy to allow anonymous read access
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        self.__client.set_bucket_policy(bucket_name, json.dumps(policy))
        logger.info(f"Set public read policy for bucket: {bucket_name}")

    def upload_file(
        self, file_data: BytesIO, file_name: str, content_type: str = None
    ) -> str:
        """
        Upload a file to MinIO storage.
        
        Args:
            file_data: File data as BytesIO or file-like object
            file_name: Name/path of the file in the bucket
            content_type: MIME type of the file
            
        Returns:
            The URL or path to access the file
        """
        bucket_name = settings.MINIO_BUCKET_NAME
        
        # Get file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Seek back to start
        
        # Upload file
        self.__client.put_object(
            bucket_name=bucket_name,
            object_name=file_name,
            data=file_data,
            length=file_size,
            content_type=content_type or "application/octet-stream",
        )
        
        # Return the object name/path (not the full URL)
        # The URL will be generated dynamically when needed
        return file_name

    def delete_file(self, file_name: str) -> None:
        """Delete a file from MinIO storage."""
        bucket_name = settings.MINIO_BUCKET_NAME
        self.__client.remove_object(bucket_name, file_name)

    def get_file_url(self, file_name: str) -> str:
        """
        Generate a public URL for accessing a file.
        
        Args:
            file_name: Name/path of the file in the bucket
            
        Returns:
            Public URL to access the file
        """
        bucket_name = settings.MINIO_BUCKET_NAME
        protocol = "https" if settings.MINIO_SECURE else "http"
        url = f"{protocol}://{settings.MINIO_ENDPOINT}/{bucket_name}/{file_name}"
        logger.debug(f"Generated public URL for {file_name}: {url}")
        return url


storage = Storage()
