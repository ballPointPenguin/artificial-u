#!/bin/bash
# Shared helpers for the local storage (RustFS) backup scripts. Source, don't execute.

STORAGE_CONTAINER="${STORAGE_CONTAINER:-artificial_u_rustfs}"
STORAGE_NETWORK="${STORAGE_NETWORK:-artificial_u_default}"
STORAGE_ENDPOINT="http://rustfs:9000"
STORAGE_CONSOLE_URL="http://localhost:9001"

# Run the AWS CLI against local storage.
# Usage: aws_cli [-v host_path:container_path]... <aws args...>
aws_cli() {
    local mounts=()
    while [[ "$1" == "-v" ]]; do
        mounts+=(-v "$2")
        shift 2
    done
    docker run --rm \
        --network "${STORAGE_NETWORK}" \
        "${mounts[@]}" \
        -e AWS_ACCESS_KEY_ID=minioadmin \
        -e AWS_SECRET_ACCESS_KEY=minioadmin \
        -e AWS_DEFAULT_REGION=us-east-1 \
        amazon/aws-cli:latest \
        --endpoint-url "${STORAGE_ENDPOINT}" "$@"
}

require_storage() {
    if ! docker ps --format '{{.Names}}' | grep -qx "${STORAGE_CONTAINER}"; then
        echo "❌ Local storage (RustFS) is not running."
        echo "   Start it with: docker compose up -d rustfs"
        exit 1
    fi
}
