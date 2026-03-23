#!/bin/bash

# automate.sh - Helper script to run the Name That Yankee automated workflow

# Navigate to the script's directory (project root)
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the automation script
# Usage: ./automate.sh [screenshot_path]
SCREENSHOT_PATH="$1"

if [ -z "$SCREENSHOT_PATH" ]; then
    # Default to the most recent screenshot/image in Downloads
    DOWNLOADS_DIR="$HOME/Downloads"
    # Find the most recently modified .png, .jpg, or .webp file
    MOST_RECENT=$(ls -t "$DOWNLOADS_DIR"/*.{png,jpg,jpeg,webp} 2>/dev/null | head -n 1)
    
    if [ -n "$MOST_RECENT" ]; then
        echo "💡 No screenshot path provided. Using most recent image: $(basename "$MOST_RECENT")"
        SCREENSHOT_PATH="$MOST_RECENT"
    fi
fi

if [ -n "$SCREENSHOT_PATH" ]; then
    python3 page-generator/main.py --automate-workflow "$SCREENSHOT_PATH"
else
    # If still no path (no images in Downloads), run without args to trigger the interactive prompt
    python3 page-generator/main.py --automate-workflow
fi
