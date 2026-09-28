#!/bin/bash
set -e

# Local storage (RustFS) sync utility - quick commands for backup operations
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=storage_lib.sh
source "${SCRIPT_DIR}/storage_lib.sh"

show_usage() {
    echo "Local storage sync utility - quick backup operations"
    echo ""
    echo "USAGE:"
    echo "  $0 upload                   Upload ./backups/ to storage buckets"
    echo "  $0 download [DIR]           Download all buckets (default: ./backups/)"
    echo "  $0 audio-only [up|down]     Sync only audio files"
    echo "  $0 status                   Show storage container status"
    echo "  $0 console                  Open the RustFS web console"
    echo "  $0 list                     List bucket contents"
    echo ""
    echo "Uploads use 'aws s3 sync --delete': changed files are re-uploaded and"
    echo "objects missing from ./backups/ are removed from the bucket."
    echo ""
    echo "EXAMPLES:"
    echo "  $0 upload                   # Upload backups to storage"
    echo "  $0 download                 # Download all to ./backups/"
    echo "  $0 download ./restore       # Download all to ./restore/"
    echo "  $0 audio-only down          # Download only audio files"
    echo "  $0 list                     # Show what's in each bucket"
    echo ""
}

case "${1:-}" in
    upload)
        require_storage
        # --overwrite is accepted for backwards compatibility; sync already overwrites changed files
        echo "🔄 Uploading backups..."
        "${SCRIPT_DIR}/upload_backups.sh"
        ;;
    download)
        require_storage
        if [[ "${2:-}" == "--help" ]]; then
            "${SCRIPT_DIR}/download_backups.sh" --help
        else
            output_dir="${2:-./backups}"
            echo "📥 Downloading all buckets to ${output_dir}..."
            "${SCRIPT_DIR}/download_backups.sh" --output "${output_dir}"
        fi
        ;;
    audio-only)
        require_storage
        case "${2:-}" in
            up|upload)
                echo "🎵 Uploading audio files..."
                aws_cli -v "$(pwd)/backups/artificial-u-audio:/data:ro" \
                    s3 sync --delete --only-show-errors /data s3://artificial-u-audio
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
        echo "🔍 Local storage status:"
        if docker ps --format '{{.Names}}' | grep -qx "${STORAGE_CONTAINER}"; then
            echo "   ✅ RustFS is running"
            echo "   🌐 Console: ${STORAGE_CONSOLE_URL}"
            echo "   🔗 API: http://localhost:9000"
        else
            echo "   ❌ RustFS is not running"
            echo "   💡 Start with: docker compose up -d rustfs"
        fi
        ;;
    console)
        echo "🌐 Opening RustFS console..."
        echo "   URL: ${STORAGE_CONSOLE_URL}"
        echo "   Login: minioadmin / minioadmin"
        if command -v open >/dev/null; then
            open "${STORAGE_CONSOLE_URL}"
        elif command -v xdg-open >/dev/null; then
            xdg-open "${STORAGE_CONSOLE_URL}"
        else
            echo "   Please open the URL manually in your browser"
        fi
        ;;
    list)
        require_storage
        echo "📋 Bucket contents:"
        echo ""
        for bucket in artificial-u-audio artificial-u-images artificial-u-lectures artificial-u-exports; do
            echo "🗂️  ${bucket}:"
            aws_cli s3 ls --recursive --summarize "s3://${bucket}" | tail -2
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
