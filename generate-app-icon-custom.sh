#!/bin/bash

# Generate iOS App Icon with customizable background
# Usage: ./generate-app-icon-custom.sh [style]
# Styles: gradient (default), solid-dark, solid-light, rounded

set -e

STYLE="${1:-gradient}"
SOURCE_IMAGE="/Users/anders/nmjanitsjar/apps/band-positions/clef.png"
ICON_DIR="/Users/anders/nmjanitsjar/apps/band-positions/ios/App/App/Assets.xcassets/AppIcon.appiconset"
OUTPUT_FILE="$ICON_DIR/AppIcon-512@2x.png"

echo "🎨 Creating iOS App Icon from clef.png with style: $STYLE"

# Create a temporary directory for processing
TEMP_DIR=$(mktemp -d)
TEMP_SQUARE="$TEMP_DIR/square.png"
TEMP_BG="$TEMP_DIR/with_background.png"

# Get source dimensions
WIDTH=$(sips -g pixelWidth "$SOURCE_IMAGE" | tail -1 | awk '{print $2}')
HEIGHT=$(sips -g pixelHeight "$SOURCE_IMAGE" | tail -1 | awk '{print $2}')

# Determine the target square size
if [ $WIDTH -gt $HEIGHT ]; then
    SQUARE_SIZE=$((WIDTH + 100))
else
    SQUARE_SIZE=$((HEIGHT + 100))
fi

echo "📐 Making image square (${SQUARE_SIZE}x${SQUARE_SIZE})..."

# Center the clef on transparent background
magick "$SOURCE_IMAGE" \
    -gravity center \
    -background none \
    -extent ${SQUARE_SIZE}x${SQUARE_SIZE} \
    "$TEMP_SQUARE"

echo "🎨 Applying $STYLE background..."

case "$STYLE" in
    gradient)
        # Blue gradient (default)
        magick -size ${SQUARE_SIZE}x${SQUARE_SIZE} \
            gradient:'#0f172a-#334155' \
            "$TEMP_BG"
        ;;
    solid-dark)
        # Solid dark background
        magick -size ${SQUARE_SIZE}x${SQUARE_SIZE} \
            xc:'#0f172a' \
            "$TEMP_BG"
        ;;
    solid-light)
        # Solid light background
        magick -size ${SQUARE_SIZE}x${SQUARE_SIZE} \
            xc:'#f8fafc' \
            "$TEMP_BG"
        ;;
    rounded)
        # Rounded corners with gradient
        magick -size ${SQUARE_SIZE}x${SQUARE_SIZE} \
            gradient:'#0f172a-#334155' \
            \( +clone -alpha extract \
               -draw "fill black polygon 0,0 0,150 150,0 \
                      fill white circle 150,150 150,0" \
               \( +clone -flip \) -compose Multiply -composite \
               \( +clone -flop \) -compose Multiply -composite \
            \) -alpha off -compose CopyOpacity -composite \
            "$TEMP_BG"
        ;;
    *)
        echo "Unknown style: $STYLE"
        echo "Available styles: gradient, solid-dark, solid-light, rounded"
        rm -rf "$TEMP_DIR"
        exit 1
        ;;
esac

# Composite the clef on top of the background
magick "$TEMP_BG" "$TEMP_SQUARE" \
    -gravity center \
    -composite \
    "$TEMP_SQUARE"

echo "📏 Resizing to 1024x1024 for iOS..."

# Resize to exact 1024x1024 for iOS
sips -z 1024 1024 "$TEMP_SQUARE" --out "$OUTPUT_FILE" > /dev/null

# Clean up temp files
rm -rf "$TEMP_DIR"

echo "✅ App icon created successfully!"
echo "   Style: $STYLE"
echo "   Output: $OUTPUT_FILE"
echo "   Size: 1024x1024"
echo ""
echo "Preview variations with:"
echo "   ./generate-app-icon-custom.sh gradient"
echo "   ./generate-app-icon-custom.sh solid-dark"
echo "   ./generate-app-icon-custom.sh solid-light"
echo "   ./generate-app-icon-custom.sh rounded"
