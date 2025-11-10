#!/bin/sh
set -e

MC_ALIAS=myminio

MC_PORT="${1:-${MINIO_PORT:-9000}}"
MC_HOST="http://minio:${MC_PORT}"
MC_USER=minioadmin
MC_PASS=minioadmin

# Wait for MinIO server to be available
echo "Waiting for MinIO on ${MC_HOST}..."
until /usr/bin/mc alias set "${MC_ALIAS}" "${MC_HOST}" "${MC_USER}" "${MC_PASS}" > /dev/null 2>&1; do
    sleep 1
done
echo "MinIO is ready."

BUCKETS="artificial-u-audio artificial-u-lectures artificial-u-images artificial-u-exports artificial-u-content-logs"

for bucket in $BUCKETS; do
    if ! /usr/bin/mc ls "${MC_ALIAS}/${bucket}" >/dev/null 2>&1; then
        echo "Creating bucket: ${bucket}"
        /usr/bin/mc mb "${MC_ALIAS}/${bucket}"
    else
        echo "Bucket '${bucket}' already exists."
    fi
    echo "Setting policy for bucket: ${bucket}"
    /usr/bin/mc anonymous set download "${MC_ALIAS}/${bucket}"
done

echo "MinIO setup complete."
exit 0