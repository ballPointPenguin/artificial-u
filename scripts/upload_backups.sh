#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=storage_lib.sh
source "${SCRIPT_DIR}/storage_lib.sh"

echo "Starting backup upload to local storage..."

BACKUP_BASE="./backups"

# Function to upload a backup directory to its corresponding bucket
upload_backup() {
    local backup_dir="$1"
    local bucket_name="$2"

    echo "Uploading ${backup_dir} to ${bucket_name} bucket..."

    aws_cli -v "$(cd "${BACKUP_BASE}/${backup_dir}" && pwd):/data:ro" \
        s3 sync --delete --only-show-errors /data "s3://${bucket_name}"

    echo "✅ Completed upload for ${backup_dir}"
}

require_storage

# Upload each backup directory
upload_backup "artificial-u-audio" "artificial-u-audio"
upload_backup "artificial-u-images" "artificial-u-images"
upload_backup "artificial-u-lectures" "artificial-u-lectures"
upload_backup "artificial-u-exports" "artificial-u-exports"

echo "🎉 All backups uploaded successfully!"
echo "You can verify uploads at: ${STORAGE_CONSOLE_URL} (minioadmin/minioadmin)"
