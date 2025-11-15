#!/bin/bash

# Script to generate PWA icons from SVG source
# Requires: ImageMagick (for convert command) or sharp-cli

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$(dirname "$SCRIPT_DIR")"
PUBLIC_DIR="$WEB_DIR/public"
ICONS_DIR="$PUBLIC_DIR/icons"
SVG_SOURCE="$PUBLIC_DIR/favicon.svg"

echo "Generating PWA icons..."
echo "Source: $SVG_SOURCE"
echo "Output: $ICONS_DIR"

# Create icons directory if it doesn't exist
mkdir -p "$ICONS_DIR"

# Check if ImageMagick is available
if command -v convert &> /dev/null; then
    echo "Using ImageMagick to generate icons..."

    # Generate standard icons
    for size in 72 96 128 144 152 192 384 512; do
        echo "Generating ${size}x${size} icon..."
        convert -background none -resize "${size}x${size}" "$SVG_SOURCE" "$ICONS_DIR/icon-${size}x${size}.png"
    done

    # Generate maskable icons (with padding for safe area)
    for size in 192 512; do
        echo "Generating ${size}x${size} maskable icon..."
        # Add 20% padding for maskable icons
        padding=$((size / 5))
        inner_size=$((size - padding * 2))
        convert -background none -resize "${inner_size}x${inner_size}" "$SVG_SOURCE" \
            -gravity center -extent "${size}x${size}" \
            -background "#5d4037" -flatten \
            "$ICONS_DIR/icon-${size}x${size}-maskable.png"
    done

    echo "Icons generated successfully!"

elif command -v npx &> /dev/null; then
    echo "ImageMagick not found. You can install it or use an online tool."
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
else
    echo "Error: Neither ImageMagick nor npm is available."
    echo "Please install ImageMagick or use an online icon generator."
    exit 1
fi
