#!/bin/bash
set -e

# MinIO Sync Utility - Quick commands for backup operations
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_usage() {
    echo "MinIO Sync Utility - Quick backup operations"
    echo ""
    echo "USAGE:"
    echo "  $0 upload [--overwrite]     Upload ./backups/ to MinIO buckets"
    echo "  $0 download [DIR]           Download all buckets (default: ./backups/)"
    echo "  $0 audio-only [up|down]     Sync only audio files"
    echo "  $0 status                   Show MinIO container status"
    echo "  $0 console                  Open MinIO web console"
    echo "  $0 list                     List bucket contents"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 upload                   # Upload backups to MinIO"
    echo "  $0 upload --overwrite       # Force overwrite existing files"
    echo "  $0 download                 # Download all to ./backups/"
    echo "  $0 download ./restore       # Download all to ./restore/"
    echo "  $0 audio-only down          # Download only audio files"
    echo "  $0 list                     # Show what's in each bucket"
    echo ""
}

check_minio() {
    if ! docker ps | grep -q artificial_u_minio; then
        echo "❌ MinIO container is not running."
        echo "   Start it with: docker-compose up -d minio"
        exit 1
    fi
}

run_mc_command() {
    local cmd="$1"
    docker run --rm \
        --network artificial_u_default \
        --entrypoint sh \
        minio/mc:latest \
        -c "
            mc alias set myminio http://minio:9000 minioadmin minioadmin && \
            $cmd
        "
}

case "${1:-}" in
    upload)
        check_minio
        if [[ "${2:-}" == "--overwrite" ]]; then
            echo "🔄 Uploading with overwrite enabled..."
            # Temporarily modify upload script to add --overwrite
            sed 's/mc mirror --remove/mc mirror --remove --overwrite/g' "${SCRIPT_DIR}/upload_backups.sh" | bash
        else
            echo "🔄 Uploading backups..."
            "${SCRIPT_DIR}/upload_backups.sh"
        fi
        ;;
    download)
        check_minio
        if [[ "${2:-}" == "--help" ]]; then
            "${SCRIPT_DIR}/download_backups.sh" --help
        else
            output_dir="${2:-./backups}"
            echo "📥 Downloading all buckets to ${output_dir}..."
            "${SCRIPT_DIR}/download_backups.sh" --output "${output_dir}"
        fi
        ;;
    audio-only)
        check_minio
        case "${2:-}" in
            up|upload)
                echo "🎵 Uploading audio files..."
                docker run --rm \
                    --network artificial_u_default \
                    -v "$(pwd)/backups/artificial-u-audio:/data" \
                    --entrypoint sh \
                    minio/mc:latest \
                    -c "
                        mc alias set myminio http://minio:9000 minioadmin minioadmin && \
                        mc mirror --remove /data myminio/artificial-u-audio
                    "
                ;;
            down|download)
                echo "🎵 Downloading audio files..."
                "${SCRIPT_DIR}/download_backups.sh" --audio
                ;;
            *)
                echo "❌ Please specify 'up' or 'down' for audio-only sync"
                exit 1
                ;;
        esac
        ;;
    status)
        echo "🔍 MinIO Container Status:"
        if docker ps | grep -q artificial_u_minio; then
            echo "   ✅ MinIO is running"
            echo "   🌐 Console: http://localhost:9001"
            echo "   🔗 API: http://localhost:9000"
        else
            echo "   ❌ MinIO is not running"
            echo "   💡 Start with: docker-compose up -d minio"
        fi
        ;;
    console)
        echo "🌐 Opening MinIO Console..."
        echo "   URL: http://localhost:9001"
        echo "   Login: minioadmin / minioadmin"
        if command -v open >/dev/null; then
            open "http://localhost:9001"
        elif command -v xdg-open >/dev/null; then
            xdg-open "http://localhost:9001"
        else
            echo "   Please open the URL manually in your browser"
        fi
        ;;
    list)
        check_minio
        echo "📋 MinIO Bucket Contents:"
        echo ""
        for bucket in artificial-u-audio artificial-u-images artificial-u-lectures; do
            echo "🗂️  ${bucket}:"
            run_mc_command "mc ls --summarize myminio/${bucket}" | tail -1
            echo ""
        done
        ;;
    --help|-h|help)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
