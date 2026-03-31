#!/usr/bin/env bash
# Usage: ./_generate-image.sh "Ein Student lernt mit KI" "output-filename"
# Generates a blog cover image via OpenAI GPT-Image-1 and saves as blog/posts/img/<filename>.png

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
source "$REPO_DIR/.env"

PROMPT="$1"
FILENAME="$2"

IMG_DIR="$SCRIPT_DIR/posts/img"
mkdir -p "$IMG_DIR"

OUTFILE="$IMG_DIR/${FILENAME}.png"

# Call OpenAI Images API
RESPONSE=$(curl -s -X POST "https://api.openai.com/v1/images/generations" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(cat <<ENDJSON
{
  "model": "gpt-image-1.5",
  "prompt": "$PROMPT",
  "n": 1,
  "size": "1536x1024",
  "quality": "low"
}
ENDJSON
)")

# Extract base64 image data and save
echo "$RESPONSE" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
if 'data' in data and len(data['data']) > 0:
    img_b64 = data['data'][0].get('b64_json', '')
    if img_b64:
        with open('$OUTFILE', 'wb') as f:
            f.write(base64.b64decode(img_b64))
        print('OK: $OUTFILE')
    else:
        url = data['data'][0].get('url', '')
        if url:
            import urllib.request
            urllib.request.urlretrieve(url, '$OUTFILE')
            print('OK: $OUTFILE')
        else:
            print('ERROR: No image data in response', file=sys.stderr)
            print(json.dumps(data, indent=2), file=sys.stderr)
            sys.exit(1)
else:
    print('ERROR: API error', file=sys.stderr)
    print(json.dumps(data, indent=2), file=sys.stderr)
    sys.exit(1)
"

# Compress: resize to 800px wide, convert to optimized WebP
WEBP_FILE="$IMG_DIR/${FILENAME}.webp"
convert "$OUTFILE" -resize 800x -quality 75 "$WEBP_FILE" 2>/dev/null && rm -f "$OUTFILE" && echo "Image saved to: $WEBP_FILE" || echo "Image saved to: $OUTFILE (WebP conversion failed, keeping PNG)"
