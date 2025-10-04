#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to the frontend folder
cd "$SCRIPT_DIR/../gui/frontend" || exit 1

# Install dependencies and build the frontend
npm install
npm run build

echo "Frontend built and files transferred to $TARGET_DIR"
