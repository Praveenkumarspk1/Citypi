"""
Storage Settings

Configuration for object storage (S3-compatible, local, etc.).
"""
from pydantic import Field
from .base import BaseSettings


class StorageSettings(BaseSettings):
    """Storage configuration."""
    
    # Provider
    storage_provider: str = "minio"  # minio, s3, gcs, azure, local

    # S3/MinIO
    s3_access_key: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    s3_secret_key: str = Field(default="minioadmin123", validation_alias="MINIO_SECRET_KEY")
    s3_endpoint_url: str = Field(default="http://localhost:9000", validation_alias="MINIO_ENDPOINT")
    s3_region: str = "us-east-1"
    s3_bucket: str = Field(default="concierge-media", validation_alias="MINIO_BUCKET")
    s3_use_ssl: bool = False
    s3_verify_ssl: bool = True

    # GCS (Google Cloud Storage)
    gcs_project_id: str = Field(default="", validation_alias="GCS_PROJECT_ID")
    gcs_credentials_path: str = Field(default="", validation_alias="GCS_CREDENTIALS_PATH")
    gcs_bucket: str = ""

    # Azure Blob Storage
    azure_account_name: str = Field(default="", validation_alias="AZURE_STORAGE_ACCOUNT")
    azure_account_key: str = Field(default="", validation_alias="AZURE_STORAGE_KEY")
    azure_container: str = ""

    # Local storage
    local_storage_path: str = "./storage"
    local_storage_base_url: str = "/media"

    # Buckets
    bucket_media: str = "concierge-media"
    bucket_documents: str = "concierge-documents"
    bucket_backups: str = "concierge-backups"
    bucket_models: str = "concierge-models"
    bucket_exports: str = "concierge-exports"

    # Upload
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_mime_types: List[str] = Field(default_factory=lambda: [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/webm", "video/quicktime",
        "audio/mpeg", "audio/wav", "audio/ogg",
        "application/pdf", "text/plain",
    ])
    allowed_extensions: List[str] = Field(default_factory=lambda: [
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".mp4", ".webm", ".mov",
        ".mp3", ".wav", ".ogg",
        ".pdf", ".txt",
    ])

    # Processing
    image_max_dimension: int = 4096
    image_quality: int = 85
    image_thumbnail_sizes: List[Dict[str, int]] = Field(default_factory=lambda: [
        {"width": 150, "height": 150, "suffix": "thumb"},
        {"width": 400, "height": 300, "suffix": "small"},
        {"width": 800, "height": 600, "suffix": "medium"},
        {"width": 1200, "height": 900, "suffix": "large"},
    ])
    video_max_duration: int = 300  # 5 minutes
    audio_max_duration: int = 600  # 10 minutes

    # CDN
    cdn_enabled: bool = False
    cdn_base_url: str = ""
    cdn_cache_ttl: int = 86400

    # Signed URLs
    signed_url_expire_seconds: int = 3600
    signed_url_method: str = "GET"