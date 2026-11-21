#!/usr/bin/env bash
#
# Demo script for Gemasuara app review video.
# This script runs the CLI commands one-by-one with pauses so you can
# screen-record the complete TikTok integration flow.
#
# Usage:
#   chmod +x scripts/demo.sh
#   ./scripts/demo.sh
#
# Optional: set auto-pause in seconds (default: manual ENTER)
#   PAUSE_SECONDS=3 ./scripts/demo.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_VIDEO="/tmp/gemasuara_demo_video.mp4"
DEMO_ACCOUNT_ALIAS="demo-account"
PAUSE_SECONDS="${PAUSE_SECONDS:-}"

wait_for_continue() {
    if [ -n "$PAUSE_SECONDS" ]; then
        echo ""
        echo "Continuing in $PAUSE_SECONDS seconds..."
        sleep "$PAUSE_SECONDS"
    else
        echo ""
        echo "Press ENTER to continue..."
        read -r
    fi
}

cd "$PROJECT_DIR"

clear
echo "=========================================="
echo "  Gemasuara - Demo Recording Script"
echo "=========================================="
echo ""
echo "This script will walk you through the end-to-end flow:"
echo "  1. Authenticate with TikTok"
echo "  2. Create an account alias"
echo "  3. Add content (video + caption)"
echo "  4. Mark content as ready"
echo "  5. Post content to TikTok as draft"
echo ""
if [ -n "$PAUSE_SECONDS" ]; then
    echo "Auto-pause mode: $PAUSE_SECONDS seconds between steps"
else
    echo "Manual mode: press ENTER to advance between steps"
fi
echo ""
echo "Press ENTER to start..."
read -r

# Check prerequisites
clear
echo "=========================================="
echo "[Step 0] Checking prerequisites"
echo "=========================================="
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Please create it from .env.example first."
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg is required to create the demo video."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is required."
    exit 1
fi

echo "All prerequisites OK."

# Create a small demo video
if [ ! -f "$DEMO_VIDEO" ]; then
    echo ""
    echo "Creating demo video file..."
    ffmpeg -f lavfi -i testsrc=duration=3:size=720x1280:rate=30 -pix_fmt yuv420p "$DEMO_VIDEO" -y 2>/dev/null
fi
echo "Demo video ready: $DEMO_VIDEO"
wait_for_continue

# Step 1: Authenticate
clear
echo "=========================================="
echo "[Step 1] Authenticate with TikTok"
echo "=========================================="
echo ""
echo "Command: python main.py auth"
echo ""
echo "After running, open the URL in your browser,"
echo "login to TikTok, and paste the authorization code."
wait_for_continue
python main.py auth
wait_for_continue

# Step 2: Show accounts
clear
echo "=========================================="
echo "[Step 2] Show authenticated accounts"
echo "=========================================="
echo ""
echo "Command: python main.py accounts"
wait_for_continue
python main.py accounts
wait_for_continue

# Step 3: Create alias
clear
echo "=========================================="
echo "[Step 3] Create account alias"
echo "=========================================="
echo ""
echo "Enter the Open ID shown above:"
read -r OPEN_ID

echo ""
echo "Command: python main.py accounts alias $OPEN_ID $DEMO_ACCOUNT_ALIAS"
wait_for_continue
python main.py accounts alias "$OPEN_ID" "$DEMO_ACCOUNT_ALIAS"
wait_for_continue

# Step 4: Add content
clear
echo "=========================================="
echo "[Step 4] Add content"
echo "=========================================="
echo ""
echo "Command:"
echo "  python main.py content add \\"
echo "    --account $DEMO_ACCOUNT_ALIAS \\"
echo "    --video $DEMO_VIDEO \\"
echo "    --title 'Demo Video' \\"
echo "    --caption 'Demo post from Gemasuara #gemasuara'"
wait_for_continue
ADD_OUTPUT=$(python main.py content add \
    --account "$DEMO_ACCOUNT_ALIAS" \
    --video "$DEMO_VIDEO" \
    --title "Demo Video" \
    --caption "Demo post from Gemasuara #gemasuara" | tee /dev/tty)

# Extract content ID from output
CONTENT_ID=$(echo "$ADD_OUTPUT" | grep -oP 'Konten dibuat: \K[a-zA-Z0-9]+' || true)
if [ -z "$CONTENT_ID" ]; then
    echo ""
    echo "Could not auto-detect Content ID. Please enter it manually:"
    read -r CONTENT_ID
fi
wait_for_continue

# Step 5: List content
clear
echo "=========================================="
echo "[Step 5] List content"
echo "=========================================="
echo ""
echo "Command: python main.py content list"
wait_for_continue
python main.py content list
wait_for_continue

# Step 6: Mark as ready
clear
echo "=========================================="
echo "[Step 6] Mark content as ready"
echo "=========================================="
echo ""
echo "Command: python main.py content ready $CONTENT_ID"
wait_for_continue
python main.py content ready "$CONTENT_ID"
wait_for_continue

# Step 7: Post content
clear
echo "=========================================="
echo "[Step 7] Post content to TikTok as draft"
echo "=========================================="
echo ""
echo "Command: python main.py content post $CONTENT_ID"
wait_for_continue
python main.py content post "$CONTENT_ID"

echo ""
echo "=========================================="
echo "  Demo flow complete!"
echo "=========================================="
echo ""
echo "Next: open the TikTok mobile app and show"
echo "the video in your inbox/drafts."
echo ""
