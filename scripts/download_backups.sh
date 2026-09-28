#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=storage_lib.sh
source "${SCRIPT_DIR}/storage_lib.sh"

echo "Starting backup download from local storage..."

# Configuration
BACKUP_BASE="./backups"

# Function to download a bucket to a local directory
download_backup() {
    local bucket_name="$1"
    local local_dir="$2"

    echo "Downloading ${bucket_name} bucket to ${local_dir}..."

    # Create local directory if it doesn't exist
    mkdir -p "${local_dir}"

    aws_cli -v "$(cd "${local_dir}" && pwd):/downloads" \
        s3 sync --delete --only-show-errors "s3://${bucket_name}" /downloads

    echo "✅ Completed download for ${bucket_name}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  --all               Download all buckets (default)"
    echo "  --audio             Download only artificial-u-audio bucket"
    echo "  --images            Download only artificial-u-images bucket"
    echo "  --lectures          Download only artificial-u-lectures bucket"
    echo "  --exports           Download only artificial-u-exports bucket"
    echo "  --output DIR        Set output directory (default: ./backups)"
    echo "  --help              Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Download all buckets to ./backups/"
    echo "  $0 --audio                           # Download only audio files"
    echo "  $0 --output ./restore                # Download to ./restore/ directory"
    echo "  $0 --audio --output ./audio-backup   # Download audio to specific directory"
}

# Parse command line arguments
DOWNLOAD_ALL=true
DOWNLOAD_AUDIO=false
DOWNLOAD_IMAGES=false
DOWNLOAD_LECTURES=false
DOWNLOAD_EXPORTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            DOWNLOAD_ALL=true
            shift
            ;;
        --audio)
            DOWNLOAD_ALL=false
            DOWNLOAD_AUDIO=true
            shift
            ;;
        --images)
            DOWNLOAD_ALL=false
            DOWNLOAD_IMAGES=true
            shift
            ;;
        --lectures)
            DOWNLOAD_ALL=false
            DOWNLOAD_LECTURES=true
            shift
            ;;
        --exports)
            DOWNLOAD_ALL=false
            DOWNLOAD_EXPORTS=true
            shift
            ;;
        --output)
            BACKUP_BASE="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

require_storage

# Create base backup directory
mkdir -p "${BACKUP_BASE}"

# Download based on selected options
if [[ "$DOWNLOAD_ALL" == "true" ]]; then
    download_backup "artificial-u-audio" "${BACKUP_BASE}/artificial-u-audio"
    download_backup "artificial-u-images" "${BACKUP_BASE}/artificial-u-images"
    download_backup "artificial-u-lectures" "${BACKUP_BASE}/artificial-u-lectures"
    download_backup "artificial-u-exports" "${BACKUP_BASE}/artificial-u-exports"
else
    if [[ "$DOWNLOAD_AUDIO" == "true" ]]; then
        download_backup "artificial-u-audio" "${BACKUP_BASE}/artificial-u-audio"
    fi
    if [[ "$DOWNLOAD_IMAGES" == "true" ]]; then
        download_backup "artificial-u-images" "${BACKUP_BASE}/artificial-u-images"
    fi
    if [[ "$DOWNLOAD_LECTURES" == "true" ]]; then
        download_backup "artificial-u-lectures" "${BACKUP_BASE}/artificial-u-lectures"
    fi
    if [[ "$DOWNLOAD_EXPORTS" == "true" ]]; then
        download_backup "artificial-u-exports" "${BACKUP_BASE}/artificial-u-exports"
    fi
fi

echo ""
echo "🎉 All selected backups downloaded successfully!"
echo "📁 Files saved to: $(realpath "${BACKUP_BASE}")"
echo "🌐 You can verify bucket contents at: ${STORAGE_CONSOLE_URL} (minioadmin/minioadmin)"

# Show summary of downloaded content
echo ""
echo "📊 Download Summary:"
if [[ -d "${BACKUP_BASE}/artificial-u-audio" ]]; then
    audio_count=$(find "${BACKUP_BASE}/artificial-u-audio" -name "*.mp3" 2>/dev/null | wc -l || echo "0")
    echo "   🎵 Audio files: ${audio_count// /} MP3 files"
fi
if [[ -d "${BACKUP_BASE}/artificial-u-images" ]]; then
    image_count=$(find "${BACKUP_BASE}/artificial-u-images" -name "*.png" 2>/dev/null | wc -l || echo "0")
    echo "   🖼️  Image files: ${image_count// /} PNG files"
fi
if [[ -d "${BACKUP_BASE}/artificial-u-lectures" ]]; then
    lecture_count=$(find "${BACKUP_BASE}/artificial-u-lectures" -name "*.txt" 2>/dev/null | wc -l || echo "0")
    echo "   📚 Lecture files: ${lecture_count// /} TXT files"
fi
if [[ -d "${BACKUP_BASE}/artificial-u-exports" ]]; then
    export_count=$(find "${BACKUP_BASE}/artificial-u-exports" -name "*.zip" 2>/dev/null | wc -l || echo "0")
    echo "   📦 Export files: ${export_count// /} ZIP files"
fi
