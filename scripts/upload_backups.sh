#!/bin/bash
set -e

echo "Starting backup upload to MinIO..."

# Docker container and alias info
MC_CONTAINER="artificial_u_mc"
MC_ALIAS="myminio"
BACKUP_BASE="./backups"

# Function to upload a backup directory to its corresponding bucket
upload_backup() {
    local backup_dir="$1"
    local bucket_name="$2"

    echo "Uploading ${backup_dir} to ${bucket_name} bucket..."

    # Use docker run with proper entrypoint override
    docker run --rm \
        --network artificial_u_default \
        -v "$(pwd)/backups/${backup_dir}:/data" \
        --entrypoint sh \
        minio/mc:latest \
        -c "
            mc alias set myminio http://minio:9000 minioadmin minioadmin && \
            mc mirror --remove /data myminio/${bucket_name}
        "

    echo "✅ Completed upload for ${backup_dir}"
}

# Ensure MinIO is running
if ! docker ps | grep -q artificial_u_minio; then
    echo "❌ MinIO container is not running. Please start it with: docker-compose up -d minio"
    exit 1
fi

# Upload each backup directory
upload_backup "artificial-u-audio" "artificial-u-audio"
upload_backup "artificial-u-images" "artificial-u-images"
upload_backup "artificial-u-lectures" "artificial-u-lectures"

echo "🎉 All backups uploaded successfully!"
echo "You can verify uploads at: http://localhost:9001 (minioadmin/minioadmin)"
