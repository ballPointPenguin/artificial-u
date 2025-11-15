#!/bin/bash

# Script to generate PWA icons from PNG source
# Requires: ImageMagick (for magick command)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$(dirname "$SCRIPT_DIR")"
PUBLIC_DIR="$WEB_DIR/public"
ICONS_DIR="$PUBLIC_DIR/icons"
PNG_SOURCE="$WEB_DIR/AU-icon.png"

echo "Generating PWA icons..."
echo "Source: $PNG_SOURCE"
echo "Output: $ICONS_DIR"

# Create icons directory if it doesn't exist
mkdir -p "$ICONS_DIR"

# Check if ImageMagick is available
if command -v magick &> /dev/null; then
    echo "Using ImageMagick to generate icons..."

    # Check if source PNG exists
    if [ ! -f "$PNG_SOURCE" ]; then
        echo "Error: Source PNG file not found at $PNG_SOURCE"
        exit 1
    fi

    # Generate standard icons
    for size in 72 96 128 144 152 192 384 512; do
        echo "Generating ${size}x${size} icon..."
        magick "$PNG_SOURCE" -resize "${size}x${size}" "$ICONS_DIR/icon-${size}x${size}.png"
    done

    # Generate maskable icons (with padding for safe area)
    for size in 192 512; do
        echo "Generating ${size}x${size} maskable icon..."
        # Add 20% padding for maskable icons
        padding=$((size / 5))
        inner_size=$((size - padding * 2))
        magick "$PNG_SOURCE" -resize "${inner_size}x${inner_size}" \
            -gravity center -background "#5d4037" -extent "${size}x${size}" \
            "$ICONS_DIR/icon-${size}x${size}-maskable.png"
    done

    echo "Icons generated successfully!"

else
    echo "Error: ImageMagick not found."
    echo "To install ImageMagick:"
    echo "  - Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "  - macOS: brew install imagemagick"
    echo "  - Windows: Download from https://imagemagick.org/script/download.php"
    echo ""
    echo "Alternatively, you can use an online PWA icon generator:"
    echo "  - https://www.pwabuilder.com/imageGenerator"
    echo "  - https://realfavicongenerator.net/"
    echo ""
    echo "Place the generated icons in: $ICONS_DIR"
    exit 1
fi
