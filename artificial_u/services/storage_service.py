"""
Storage service for handling S3/MinIO operations in ArtificialU.

This service abstracts storage operations for files, allowing the application
to work with either local MinIO (development) or AWS S3 (production).
"""

import asyncio
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from artificial_u.config import get_settings


class StorageService:
    """Service for handling file storage operations with S3/MinIO compatibility."""

    def __init__(self, logger=None):
        """
        Initialize the storage service with appropriate client.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.settings = get_settings()

        # Initialize S3 client
        self.client = self._get_s3_client()

        # Set bucket names from configuration
        self.audio_bucket = self.settings.STORAGE_AUDIO_BUCKET
        self.lectures_bucket = self.settings.STORAGE_LECTURES_BUCKET
        self.images_bucket = self.settings.STORAGE_IMAGES_BUCKET
        self.exports_bucket = self.settings.STORAGE_EXPORTS_BUCKET
        self.content_logs_bucket = self.settings.STORAGE_CONTENT_LOGS_BUCKET

        self.logger.info(
            f"StorageService initialized with buckets: "
            f"audio={self.audio_bucket}, lectures={self.lectures_bucket}, "
            f"images={self.images_bucket}, exports={self.exports_bucket}, "
            f"content_logs={self.content_logs_bucket}"
        )

    def _get_s3_client(self):
        """
        Get appropriate S3 client based on environment.

        Returns:
            boto3.client: Configured S3 client
        """
        # Get settings
        storage_type = self.settings.STORAGE_TYPE

        # Use local MinIO in development
        if storage_type == "minio":
            self.logger.info(f"Using MinIO at {self.settings.STORAGE_ENDPOINT_URL}")
            return boto3.client(
                "s3",
                endpoint_url=self.settings.STORAGE_ENDPOINT_URL,
                aws_access_key_id=self.settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=self.settings.STORAGE_SECRET_KEY,
                config=Config(signature_version="s3v4"),
                region_name=self.settings.STORAGE_REGION,
            )
        # Use real AWS S3 in production
        else:
            self.logger.info(f"Using AWS S3 in region {self.settings.STORAGE_REGION}")
            # Check if explicit credentials are provided
            if self.settings.STORAGE_ACCESS_KEY and self.settings.STORAGE_SECRET_KEY:
                self.logger.info("Using explicit AWS credentials from environment")
                return boto3.client(
                    "s3",
                    aws_access_key_id=self.settings.STORAGE_ACCESS_KEY,
                    aws_secret_access_key=self.settings.STORAGE_SECRET_KEY,
                    region_name=self.settings.STORAGE_REGION,
                )
            else:
                # Use IAM role credentials (for ECS tasks in production)
                self.logger.info("Using IAM role credentials for S3 access")
                return boto3.client(
                    "s3",
                    region_name=self.settings.STORAGE_REGION,
                )

    async def upload_file(
        self, file_data: bytes, bucket: str, object_name: str, content_type: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload file data to storage.

        Args:
            file_data: Binary file data
            bucket: Bucket name
            object_name: Object key/name
            content_type: Content type of the file

        Returns:
            Tuple of (success, url)
        """
        try:
            self.logger.info(f"Attempting to upload to bucket '{bucket}' with key '{object_name}'")
            file_obj = io.BytesIO(file_data)

            # Set extra arguments like content type if provided
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            # Upload to S3/MinIO (blocking) in a thread
            await asyncio.to_thread(
                self.client.upload_fileobj, file_obj, bucket, object_name, ExtraArgs=extra_args
            )

            # Generate URL
            url = self.get_file_url(bucket, object_name)
            self.logger.info(f"Successfully uploaded file to {bucket}/{object_name}, URL: {url}")
            return True, url
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            self.logger.error(
                f"AWS ClientError uploading to {bucket}/{object_name}: "
                f"Code={error_code}, Message={error_msg}",
                exc_info=True,
            )
            return False, None
        except Exception as e:
            self.logger.error(
                f"Unexpected error uploading to {bucket}/{object_name}: {str(e)}",
                exc_info=True,
            )
            return False, None

    async def upload_audio_file(
        self, file_data: bytes, object_name: str, content_type: str = "audio/mpeg"
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload audio file data to storage.

        Args:
            file_data: Binary file data
            object_name: Object key/name
            content_type: Content type of the audio file

        Returns:
            Tuple of (success, url)
        """
        return await self.upload_file(
            file_data, self.audio_bucket, object_name, content_type=content_type
        )

    async def upload_lecture_file(
        self, file_data: bytes, object_name: str, content_type: str = "text/markdown"
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload lecture file data to storage.

        Args:
            file_data: Binary file data
            object_name: Object key/name
            content_type: Content type of the lecture file

        Returns:
            Tuple of (success, url)
        """
        return await self.upload_file(
            file_data, self.lectures_bucket, object_name, content_type=content_type
        )

    async def upload_export_file(
        self, file_data: bytes, object_name: str, content_type: str = "application/zip"
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload export file data to storage.

        Args:
            file_data: Binary file data
            object_name: Object key/name
            content_type: Content type of the export file

        Returns:
            Tuple of (success, url)
        """
        return await self.upload_file(
            file_data, self.exports_bucket, object_name, content_type=content_type
        )

    async def upload_content_log(
        self, file_data: bytes, object_name: str, content_type: str = "application/json"
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload content log file data to storage.

        Args:
            file_data: Binary file data
            object_name: Object key/name
            content_type: Content type of the log file

        Returns:
            Tuple of (success, url)
        """
        return await self.upload_file(
            file_data, self.content_logs_bucket, object_name, content_type=content_type
        )

    def get_file_url(self, bucket: str, object_name: str, download: bool = False) -> str:
        """
        Generate URL for a stored file.

        Args:
            bucket: Bucket name
            object_name: Object key/name
            download: If True, generate URL with Content-Disposition header for downloads

        Returns:
            Public URL for the file (presigned if download=True)
        """
        if download:
            # Generate presigned URL with download headers
            return self.get_download_url(bucket, object_name)

        storage_type = self.settings.STORAGE_TYPE

        if storage_type == "minio":
            # Local MinIO URL using the configured endpoint
            base_url = self.settings.STORAGE_PUBLIC_URL.rstrip("/")

            # Ensure we have a proper URL
            if not base_url:
                self.logger.warning("STORAGE_PUBLIC_URL not set, using endpoint URL instead")
                base_url = self.settings.STORAGE_ENDPOINT_URL

            # Combine all parts to create the full URL
            return f"{base_url}/{bucket}/{object_name}"
        else:
            # AWS S3 URL
            return f"https://{bucket}.s3.{self.settings.STORAGE_REGION}.amazonaws.com/{object_name}"

    def get_download_url(
        self, bucket: str, object_name: str, expires_in: int = 3600, filename: str = None
    ) -> str:
        """
        Generate a presigned URL for downloading a file with Content-Disposition header.

        This ensures the browser prompts for download instead of opening the file,
        which is especially important for mobile browsers.

        Args:
            bucket: Bucket name
            object_name: Object key/name
            expires_in: URL expiration time in seconds (default: 1 hour)
            filename: Optional custom filename for download (defaults to object_name)

        Returns:
            Presigned URL with download headers
        """
        try:
            # Use the object name as filename if not provided
            if not filename:
                filename = object_name.split("/")[-1]  # Get last part of path

            # Generate presigned URL with Content-Disposition header
            url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket,
                    "Key": object_name,
                    "ResponseContentDisposition": f'attachment; filename="{filename}"',
                },
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            self.logger.error(
                f"Error generating download URL for {bucket}/{object_name}: {str(e)}"
            )
            # Fall back to regular URL if presigned URL generation fails
            return self.get_file_url(bucket, object_name)

    async def download_file(
        self, bucket: str, object_name: str
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download a file from storage.

        Args:
            bucket: Bucket name
            object_name: Object key/name

        Returns:
            Tuple of (file_data, content_type)
        """
        try:
            # Create a file-like object to hold the downloaded content
            file_obj = io.BytesIO()

            # Get content type (blocking)
            response = await asyncio.to_thread(
                self.client.head_object, Bucket=bucket, Key=object_name
            )
            content_type = response.get("ContentType", "application/octet-stream")

            # Download file (blocking)
            await asyncio.to_thread(self.client.download_fileobj, bucket, object_name, file_obj)
            file_obj.seek(0)

            self.logger.info(f"Downloaded file from {bucket}/{object_name}")
            return file_obj.read(), content_type
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                self.logger.warning(f"File not found: {bucket}/{object_name}")
            else:
                self.logger.error(f"Error downloading file: {str(e)}")
            return None, None
        except Exception as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            return None, None

    async def download_audio_file(self, object_name: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download an audio file from storage.

        Args:
            object_name: Object key/name

        Returns:
            Tuple of (file_data, content_type)
        """
        return await self.download_file(self.audio_bucket, object_name)

    async def download_lecture_file(
        self, object_name: str
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download a lecture file from storage.

        Args:
            object_name: Object key/name

        Returns:
            Tuple of (file_data, content_type)
        """
        return await self.download_file(self.lectures_bucket, object_name)

    async def delete_file(self, bucket: str, object_name: str) -> bool:
        """
        Delete a file from storage.

        Args:
            bucket: Bucket name
            object_name: Object key/name

        Returns:
            Success flag
        """
        try:
            await asyncio.to_thread(self.client.delete_object, Bucket=bucket, Key=object_name)
            self.logger.info(f"Deleted file from {bucket}/{object_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting file: {str(e)}")
            return False

    async def list_files(
        self, bucket: str, prefix: Optional[str] = None, max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List files in a bucket.

        Args:
            bucket: Bucket name
            prefix: Optional prefix to filter by
            max_keys: Maximum number of keys to return

        Returns:
            List of file objects with metadata
        """
        try:
            # Prepare list parameters
            params = {"Bucket": bucket, "MaxKeys": max_keys}
            if prefix:
                params["Prefix"] = prefix

            # List objects (blocking)
            response = await asyncio.to_thread(self.client.list_objects_v2, **params)

            # Process results
            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    # Get additional metadata (blocking)
                    head = await asyncio.to_thread(
                        self.client.head_object, Bucket=bucket, Key=obj["Key"]
                    )

                    files.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                            "content_type": head.get("ContentType", "application/octet-stream"),
                            "url": self.get_file_url(bucket, obj["Key"]),
                        }
                    )

            return files
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return []

    def generate_audio_key(
        self,
        course_code: str,
        week_number: int,
        lecture_order: int,
        extension: str = "mp3",
    ) -> str:
        """
        Generate a standard object key for a lecture audio file.

        Args:
            course_code: Course code (human-friendly)
            week_number: Week number
            lecture_order: Lecture order within week
            extension: File extension (default: mp3)

        Returns:
            Object key for S3/MinIO
        """
        return f"{course_code}/{course_code}_{week_number}_{lecture_order}.{extension}"

    def generate_lecture_key(
        self,
        course_code: str,
        week_number: int,
        lecture_order: int,
        extension: str = "md",
    ) -> str:
        """
        Generate a standard object key for a lecture text file.

        Args:
            course_code: Course code (human-friendly)
            week_number: Week number
            lecture_order: Lecture order within week
            extension: File extension (default: md)

        Returns:
            Object key for S3/MinIO
        """
        return f"{course_code}/{course_code}_{week_number}_{lecture_order}.{extension}"

    def parse_storage_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a storage URL to extract bucket and object key.

        Args:
            url: Storage URL (MinIO or S3 format)

        Returns:
            Tuple of (bucket, object_key) or (None, None) if parsing fails
        """
        if not url:
            return None, None

        try:
            # Handle MinIO URL format: http://localhost:9000/bucket/key
            if self.settings.STORAGE_TYPE == "minio":
                # Remove the base URL
                base_url = self.settings.STORAGE_PUBLIC_URL.rstrip("/")
                if url.startswith(base_url):
                    path = url[len(base_url) :].lstrip("/")
                    # Split into bucket and key
                    parts = path.split("/", 1)
                    if len(parts) == 2:
                        return parts[0], parts[1]

            # Handle S3 URL format: https://bucket.s3.region.amazonaws.com/key
            elif ".s3." in url and ".amazonaws.com/" in url:
                # Extract bucket from subdomain
                start = url.find("://") + 3
                end = url.find(".s3.")
                bucket = url[start:end]

                # Extract key after the domain
                key_start = url.find(".amazonaws.com/") + 15
                key = url[key_start:]

                if bucket and key:
                    return bucket, key

            self.logger.warning(f"Could not parse storage URL: {url}")
            return None, None

        except Exception as e:
            self.logger.error(f"Error parsing storage URL {url}: {str(e)}")
            return None, None
