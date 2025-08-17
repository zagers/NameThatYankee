#!/bin/bash

# Create the output directory if it doesn't exist
mkdir -p webp_images

# Loop through all JPG files
for file in answer*.webp; do
  if [ -f "$file" ]; then
    echo "Processing $file..."
    sharp \
      --input "$file" \
      --output "webp_images/${file%.*}.webp" \
      --format webp \
      --quality 100 \
      resize 375
  fi
done

echo "Batch processing complete."

