#!/bin/sh
# Create local storage buckets and apply public-read + CORS settings.
# Runs as the docker compose `storage-setup` service (amazon/aws-cli image) against RustFS.
# Idempotent: safe to re-run; policy and CORS are re-applied every time.
set -e

ENDPOINT="${STORAGE_ENDPOINT:-http://rustfs:9000}"
BUCKETS="artificial-u-audio artificial-u-lectures artificial-u-images artificial-u-exports artificial-u-content-logs"

s3api() {
    aws --endpoint-url "${ENDPOINT}" s3api "$@"
}

# Match production (cdk_stack.py): browsers fetch timelines/media cross-origin
CORS='{"CORSRules":[{"AllowedOrigins":["*"],"AllowedMethods":["GET","HEAD"],"AllowedHeaders":["*"],"ExposeHeaders":["Content-Length","Content-Range","Accept-Ranges"],"MaxAgeSeconds":3600}]}'

for bucket in $BUCKETS; do
    if s3api head-bucket --bucket "${bucket}" >/dev/null 2>&1; then
        echo "Bucket '${bucket}' already exists."
    else
        echo "Creating bucket: ${bucket}"
        s3api create-bucket --bucket "${bucket}" >/dev/null
    fi

    policy='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::'"${bucket}"'/*"]}]}'
    s3api put-bucket-policy --bucket "${bucket}" --policy "${policy}"
    s3api put-bucket-cors --bucket "${bucket}" --cors-configuration "${CORS}"
    echo "Applied public-read policy and CORS to ${bucket}"
done

echo "Storage setup complete."
