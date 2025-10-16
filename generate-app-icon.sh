#!/bin/bash

# Generate iOS App Icon from clef.png
# This script creates a 1024x1024 app icon with proper padding and background

set -e

SOURCE_IMAGE="/Users/anders/nmjanitsjar/apps/band-positions/clef.png"
ICON_DIR="/Users/anders/nmjanitsjar/apps/band-positions/ios/App/App/Assets.xcassets/AppIcon.appiconset"
OUTPUT_FILE="$ICON_DIR/AppIcon-512@2x.png"

echo "🎨 Creating iOS App Icon from clef.png..."

# Create a temporary directory for processing
TEMP_DIR=$(mktemp -d)
TEMP_SQUARE="$TEMP_DIR/square.png"
TEMP_BG="$TEMP_DIR/with_background.png"

echo "📐 Making image square with padding..."

# Get source dimensions
WIDTH=$(sips -g pixelWidth "$SOURCE_IMAGE" | tail -1 | awk '{print $2}')
HEIGHT=$(sips -g pixelHeight "$SOURCE_IMAGE" | tail -1 | awk '{print $2}')

echo "   Source dimensions: ${WIDTH}x${HEIGHT}"

# Determine the target square size (use the larger dimension + padding)
if [ $WIDTH -gt $HEIGHT ]; then
    SQUARE_SIZE=$((WIDTH + 100))
else
    SQUARE_SIZE=$((HEIGHT + 100))
fi

echo "   Square size: ${SQUARE_SIZE}x${SQUARE_SIZE}"

# Create a square image with transparent background and center the clef
# Using ImageMagick (magick) for better control
magick "$SOURCE_IMAGE" \
    -gravity center \
    -background none \
    -extent ${SQUARE_SIZE}x${SQUARE_SIZE} \
    "$TEMP_SQUARE"

echo "🎨 Adding background gradient..."

# Create a nice gradient background (blue theme matching the app)
magick -size ${SQUARE_SIZE}x${SQUARE_SIZE} \
    gradient:'#0f172a-#334155' \
    "$TEMP_BG"

# Composite the clef on top of the background
magick "$TEMP_BG" "$TEMP_SQUARE" \
    -gravity center \
    -composite \
    "$TEMP_SQUARE"

echo "📏 Resizing to 1024x1024 for iOS..."

# Resize to exact 1024x1024 for iOS
sips -z 1024 1024 "$TEMP_SQUARE" --out "$OUTPUT_FILE" > /dev/null

echo "✅ App icon created successfully!"
echo "   Output: $OUTPUT_FILE"
echo "   Size: 1024x1024"

# Clean up temp files
rm -rf "$TEMP_DIR"

echo ""
echo "🔄 Next steps:"
echo "   1. Open Xcode: npx cap open ios"
echo "   2. Clean build folder: Product > Clean Build Folder"
echo "   3. Build and run the app"
echo ""
echo "The new app icon will appear on your device!"
