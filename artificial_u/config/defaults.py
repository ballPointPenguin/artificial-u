"""
Default configuration values for the ArtificialU system.
"""

# Database defaults
DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/artificial_u_dev"

# Audio defaults (temporary path for processing)
DEFAULT_TEMP_AUDIO_PATH = "temp_audio"

# Content generation defaults
DEFAULT_CONTENT_BACKEND = "anthropic"
DEFAULT_OLLAMA_MODEL = "phi4-mini"

# Storage defaults (MinIO/S3)
DEFAULT_STORAGE_TYPE = "minio"  # "minio" or "s3"
DEFAULT_STORAGE_ENDPOINT_URL = "http://localhost:9000"
DEFAULT_STORAGE_PUBLIC_URL = "http://localhost:9000"  # For public access URLs
DEFAULT_STORAGE_ACCESS_KEY = "minioadmin"
DEFAULT_STORAGE_SECRET_KEY = "minioadmin"
DEFAULT_STORAGE_REGION = "us-east-1"
DEFAULT_STORAGE_AUDIO_BUCKET = "artificial-u-audio"
DEFAULT_STORAGE_LECTURES_BUCKET = "artificial-u-lectures"
DEFAULT_STORAGE_IMAGES_BUCKET = "artificial-u-images"

# Department and specialization defaults
DEPARTMENTS = [
    "Computer Science",
    "Physics",
    "Biology",
    "Mathematics",
    "History",
    "Psychology",
    "Chemistry",
    "Engineering",
    "Economics",
    "Philosophy",
]

# Course defaults
DEFAULT_COURSE_WEEKS = 14
DEFAULT_LECTURES_PER_WEEK = 1
DEFAULT_LECTURE_WORD_COUNT = 2000

# Logging defaults
DEFAULT_LOG_LEVEL = "INFO"
