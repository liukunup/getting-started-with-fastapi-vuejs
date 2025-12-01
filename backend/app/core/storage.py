from minio import Minio

from app.core.config import settings


class Storage:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

    def ensure_bucket_exists(self, bucket_name: str):
        if not self.client.bucket_exists(bucket_name=bucket_name):
            self.client.make_bucket(bucket_name=bucket_name)

    def upload_file(self, file_data, file_name: str, content_type: str) -> str:
        self.ensure_bucket_exists(settings.MINIO_BUCKET_NAME)
        self.client.put_object(
            settings.MINIO_BUCKET_NAME,
            file_name,
            file_data,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=content_type,
        )
        # Return the URL (assuming public bucket or presigned url needed, for now just path)
        # In a real scenario, you might want to generate a presigned URL or serve via a proxy.
        # For simplicity, we'll assume the frontend can access minio directly or we serve it.
        # Let's return the object name for now.
        return file_name


storage = Storage()
