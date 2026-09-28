#!/bin/bash
# One-time migration of local object storage from MinIO to RustFS.
#
# RustFS reads MinIO's single-drive data layout in place, so this copies the old
# MinIO volume into the new RustFS volume. The old volume is left untouched as a
# backup; delete it yourself once you've verified everything:
#   docker volume rm artificial_u_minio_data
set -euo pipefail

OLD_CONTAINER="artificial_u_minio"
OLD_VOLUME="artificial_u_minio_data"
NEW_VOLUME="artificial_u_rustfs_data"
RUSTFS_UID=10001

if ! docker volume inspect "${OLD_VOLUME}" >/dev/null 2>&1; then
    echo "No ${OLD_VOLUME} volume found; nothing to migrate."
    exit 0
fi

if docker volume inspect "${NEW_VOLUME}" >/dev/null 2>&1 &&
    [ -n "$(docker run --rm -v "${NEW_VOLUME}:/d" alpine ls -A /d)" ]; then
    echo "❌ ${NEW_VOLUME} already contains data; refusing to overwrite it."
    exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "${OLD_CONTAINER}"; then
    echo "Stopping and removing the old ${OLD_CONTAINER} container (its volume is kept)..."
    docker rm -f "${OLD_CONTAINER}" >/dev/null
fi

# Labels let docker compose adopt the volume as the `rustfs_data` volume without warnings
docker volume create \
    --label com.docker.compose.project=artificial_u \
    --label com.docker.compose.volume=rustfs_data \
    "${NEW_VOLUME}" >/dev/null

echo "Copying ${OLD_VOLUME} -> ${NEW_VOLUME}..."
docker run --rm \
    -v "${OLD_VOLUME}:/src:ro" \
    -v "${NEW_VOLUME}:/dst" \
    alpine sh -c "cp -a /src/. /dst/ && chown -R ${RUSTFS_UID}:${RUSTFS_UID} /dst && du -sh /dst"

echo "✅ Done. Start RustFS with: docker compose up -d"
