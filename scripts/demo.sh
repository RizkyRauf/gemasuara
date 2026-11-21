#!/usr/bin/env bash
#
# Demo script for Gemasuara app review video.
# This script runs the CLI commands one-by-one with pauses so you can
# screen-record the complete TikTok integration flow.
#
# Usage:
#   chmod +x scripts/demo.sh
#   ./scripts/demo.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_VIDEO="/tmp/gemasuara_demo_video.mp4"
DEMO_ACCOUNT_ALIAS="demo-account"

cd "$PROJECT_DIR"

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
echo "Press ENTER to start..."
read -r

# Check prerequisites
echo ""
echo "[Step 0] Checking prerequisites..."
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

# Create a small demo video
if [ ! -f "$DEMO_VIDEO" ]; then
    echo "[Step 0] Creating demo video file..."
    ffmpeg -f lavfi -i testsrc=duration=3:size=720x1280:rate=30 -pix_fmt yuv420p "$DEMO_VIDEO" -y 2>/dev/null
fi
echo "Demo video ready: $DEMO_VIDEO"
echo ""
echo "Press ENTER to continue..."
read -r

# Step 1: Authenticate
echo ""
echo "=========================================="
echo "[Step 1] Authenticate with TikTok"
echo "=========================================="
echo ""
echo "The following command will generate an OAuth URL."
echo "Please open the URL in your browser, login, and copy the authorization code."
echo ""
echo "Press ENTER to run: python main.py auth"
read -r
python main.py auth

echo ""
echo "Press ENTER to continue..."
read -r

# Step 2: Show accounts
echo ""
echo "=========================================="
echo "[Step 2] Show authenticated accounts"
echo "=========================================="
echo ""
echo "Press ENTER to run: python main.py accounts"
read -r
python main.py accounts

echo ""
echo "Press ENTER to continue..."
read -r

# Step 3: Create alias
echo ""
echo "=========================================="
echo "[Step 3] Create account alias"
echo "=========================================="
echo ""
echo "Enter the Open ID from the account above:"
read -r OPEN_ID

echo ""
echo "Press ENTER to run: python main.py accounts alias $OPEN_ID $DEMO_ACCOUNT_ALIAS"
read -r
python main.py accounts alias "$OPEN_ID" "$DEMO_ACCOUNT_ALIAS"

echo ""
echo "Press ENTER to continue..."
read -r

# Step 4: Add content
echo ""
echo "=========================================="
echo "[Step 4] Add content"
echo "=========================================="
echo ""
echo "Press ENTER to run: python main.py content add --account $DEMO_ACCOUNT_ALIAS --video $DEMO_VIDEO --title 'Demo Video' --caption 'This is a demo post for Gemasuara #demo #gemasuara'"
read -r
python main.py content add \
    --account "$DEMO_ACCOUNT_ALIAS" \
    --video "$DEMO_VIDEO" \
    --title "Demo Video" \
    --caption "This is a demo post for Gemasuara #demo #gemasuara"

echo ""
echo "Press ENTER to continue..."
read -r

# Step 5: List content
echo ""
echo "=========================================="
echo "[Step 5] List content"
echo "=========================================="
echo ""
echo "Press ENTER to run: python main.py content list"
read -r
python main.py content list

echo ""
echo "Press ENTER to continue..."
read -r

# Step 6: Get content ID
echo ""
echo "Enter the Content ID from the list above:"
read -r CONTENT_ID

# Step 7: Mark as ready
echo ""
echo "=========================================="
echo "[Step 6] Mark content as ready"
echo "=========================================="
echo ""
echo "Press ENTER to run: python main.py content ready $CONTENT_ID"
read -r
python main.py content ready "$CONTENT_ID"

echo ""
echo "Press ENTER to continue..."
read -r

# Step 8: Post content
echo ""
echo "=========================================="
echo "[Step 7] Post content to TikTok as draft"
echo "=========================================="
echo ""
echo "Press ENTER to run: python main.py content post $CONTENT_ID"
read -r
python main.py content post "$CONTENT_ID"

echo ""
echo "=========================================="
echo "  Demo flow complete!"
echo "=========================================="
echo ""
echo "Now open the TikTok mobile app to show the video in your inbox/drafts."
echo ""
