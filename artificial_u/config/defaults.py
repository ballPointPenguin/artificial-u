"""
Default configuration values for the ArtificialU system.
"""

# Database defaults
DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/artificial_u_dev"

# Database connection pool defaults
# These are conservative values appropriate for a db.t4g.small (~110 max_connections)
# with room for admin connections and the new rds_reserved feature
DEFAULT_DB_POOL_SIZE = 5  # Minimum connections maintained in the pool
DEFAULT_DB_MAX_OVERFLOW = 10  # Additional connections allowed beyond pool_size
DEFAULT_DB_POOL_TIMEOUT = 30  # Seconds to wait for a connection from pool
DEFAULT_DB_POOL_RECYCLE = 1800  # Recycle connections after 30 minutes (avoids stale connections)
DEFAULT_DB_POOL_PRE_PING = True  # Test connections before use (handles RDS failovers)

# Content generation defaults
DEFAULT_CONTENT_BACKEND = "anthropic"
DEFAULT_CONTENT_LOGS_PATH = "content_logs"

# TTS defaults
DEFAULT_TTS_BACKEND = "elevenlabs"
DEFAULT_XAI_TTS_BASE_URL = "https://api.x.ai/v1"
DEFAULT_XAI_TTS_LANGUAGE = "en"
DEFAULT_QWEN_TTS_MODEL = "qwen-audio-3.0-tts-flash"
# Alibaba Model Studio WebSocket endpoint. qwen-audio-3.0-tts is served only
# from the Singapore and Beijing regions (NOT us-east-1/Virginia, which 404s
# on the websocket route), so the ALIBABA_API_KEY must be a Singapore- or
# Beijing-region key. Singapore -> dashscope-intl, Beijing -> dashscope.
DEFAULT_ALIBABA_TTS_WSS_URL = "wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference"

# Storage defaults (MinIO/S3)
DEFAULT_STORAGE_TYPE = "minio"  # "minio" or "s3"
DEFAULT_STORAGE_ENDPOINT_URL = "http://localhost:9000"
DEFAULT_STORAGE_PUBLIC_URL = "http://localhost:9000"  # For public access URLs
DEFAULT_STORAGE_REGION = "us-east-1"
DEFAULT_STORAGE_AUDIO_BUCKET = "artificial-u-audio"
DEFAULT_STORAGE_LECTURES_BUCKET = "artificial-u-lectures"
DEFAULT_STORAGE_IMAGES_BUCKET = "artificial-u-images"
DEFAULT_STORAGE_EXPORTS_BUCKET = "artificial-u-exports"
DEFAULT_STORAGE_CONTENT_LOGS_BUCKET = "artificial-u-content-logs"

# Course defaults
DEFAULT_LECTURE_WORD_COUNT = 3000
DEFAULT_LECTURE_IMAGE_INTERVAL_SEC = 45

# Logging defaults
DEFAULT_LOG_LEVEL = "INFO"
