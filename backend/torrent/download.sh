#!/bin/bash

DOWNLOAD_DIR="/downloads"
TORRENT_URL="https://academictorrents.com/download/56aa49f9653ba545f48df2e33679f014d2829c10.torrent"
TORRENT_FILE="/app/trigeminal.torrent"

# Files to keep
KEEP_FILES=(
    "./reddit/subreddits23/TrigeminalNeuralgia_comments.zst"
    "./reddit/subreddits23/TrigeminalNeuralgia_submissions.zst"
)

echo "Step 1: Fetching .torrent file..."
curl -sSL "$TORRENT_URL" -o "$TORRENT_FILE"

if [ ! -f "$TORRENT_FILE" ]; then
    echo "❌ Failed to download .torrent file!"
    exit 1
fi
echo "✅ Torrent file saved: $TORRENT_FILE"

echo "Step 2: Listing torrent contents..."
FILE_LIST="$(aria2c --show-files "$TORRENT_FILE")"
echo "🔹 Full file list from torrent:"
echo "$FILE_LIST"

# Function to find the index of a file in the torrent list
get_file_index() {
    local target="$1"
    echo "$FILE_LIST" | awk -v target="$target" '
        /^[0-9]+\|/ {
            split($0, arr, "|")
            idx = arr[1]        # 79895
            path = arr[2]       # ./reddit/subreddits23/zyzz_submissions.zst
            gsub(/^[ \t]+|[ \t]+$/, "", path)  # trim spaces (if any)
            if (path == target) {
                print idx
                exit
            }
        }
    '
}

# Find indexes of both files
FILE_INDEX_1=$(get_file_index "${KEEP_FILES[0]}")
FILE_INDEX_2=$(get_file_index "${KEEP_FILES[1]}")

# Ensure we found both files
if [ -z "$FILE_INDEX_1" ] || [ -z "$FILE_INDEX_2" ]; then
    echo "❌ One or both target files not found in torrent!"
    exit 1
fi

echo "✅ Found indexes: ${KEEP_FILES[0]} -> $FILE_INDEX_1"
echo "✅ Found indexes: ${KEEP_FILES[1]} -> $FILE_INDEX_2"

echo "Step 3: Downloading ONLY the required files..."
aria2c \
  --dir="$DOWNLOAD_DIR" \
  --select-file="$FILE_INDEX_1,$FILE_INDEX_2" \
  --seed-time=0 \
  "$TORRENT_FILE"

echo "✅ Download complete! Now cleaning up unwanted files..."

# Delete everything in reddit/subreddits23/ EXCEPT the two target files
find "$DOWNLOAD_DIR/reddit/subreddits23" -type f ! -name "TrigeminalNeuralgia_comments.zst" ! -name "TrigeminalNeuralgia_submissions.zst" -delete

echo "✅ Cleanup complete! Only the required files remain."
