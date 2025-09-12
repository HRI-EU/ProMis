#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to the frontend folder
cd "$SCRIPT_DIR/gui/frontend" || exit 1

# Install dependencies and build the frontend
npm install
npm run build

# Define the build output and target directory
BUILD_DIR="$SCRIPT_DIR/gui/frontend/build"
TARGET_DIR="$SCRIPT_DIR/promis/gui/frontend"

# Create the target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Copy the build files to the target location
cp -r "$BUILD_DIR"/* "$TARGET_DIR"/

echo "Frontend built and files transferred to $TARGET_DIR"
