#!/bin/sh
# Download Bebas Neue (SIL OFL 1.1) into ./fonts/ so libass can find it.
# Usage:  sh fetch_font.sh [dest_dir]
set -e
DEST="${1:-$(dirname "$0")/fonts}"
mkdir -p "$DEST"

CSS=$(curl -fsSL "https://fonts.googleapis.com/css2?family=Bebas+Neue")
URL=$(printf '%s' "$CSS" | tr ')' '\n' \
      | grep -o 'https://fonts\.gstatic\.com[^ ]*\.\(ttf\|woff2\)' | tail -1)
[ -n "$URL" ] || { echo "could not resolve the font URL" >&2; exit 1; }

case "$URL" in
  *.ttf)
    curl -fsSL -o "$DEST/BebasNeue.ttf" "$URL"
    ;;
  *.woff2)
    # Google serves woff2 to modern clients; unwrap it back to a TTF that
    # fontconfig/libass will pick up. Needs: pip install fonttools brotli
    curl -fsSL -o "$DEST/BebasNeue.woff2" "$URL"
    python3 - "$DEST" <<'PY'
import sys, os
from fontTools.ttLib import TTFont
d = sys.argv[1]
src = os.path.join(d, "BebasNeue.woff2")
f = TTFont(src); f.flavor = None
f.save(os.path.join(d, "BebasNeue.ttf"))
os.remove(src)
PY
    ;;
esac

echo "wrote $DEST/BebasNeue.ttf"
echo "pass it to the generator with --fontsdir $DEST"
