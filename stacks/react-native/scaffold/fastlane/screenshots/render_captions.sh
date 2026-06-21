#!/usr/bin/env bash
# Frame raw screenshots with a brand gradient background + localized caption.
# Requires ImageMagick (`magick`). Reads ROOT (default: this dir), walks every
# <locale>/<device>/NN_*.png, and writes NN_*_framed.png next to each source.
#
# Captions: optional captions/<locale>.txt with one "NN=Caption text" per line.
# Override the gradient with GRADIENT_FROM / GRADIENT_TO (hex).
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "$0")" && pwd)}"
GRADIENT_FROM="${GRADIENT_FROM:-#7BAE7F}"
GRADIENT_TO="${GRADIENT_TO:-#4F7D5B}"
FONT="${CAPTION_FONT:-Helvetica}"
PAD="${PAD:-120}"

command -v magick >/dev/null 2>&1 || { echo "ImageMagick (magick) not found"; exit 1; }

shopt -s nullglob
for src in "$ROOT"/*/*/[0-9][0-9]_*.png; do
  case "$src" in *_framed.png) continue ;; esac
  base="$(basename "$src")"
  idx="${base%%_*}"
  loc="$(basename "$(dirname "$(dirname "$src")")")"
  caption=""
  capfile="$ROOT/captions/${loc}.txt"
  [ -f "$capfile" ] && caption="$(grep -E "^${idx}=" "$capfile" | head -1 | cut -d= -f2- || true)"

  read -r W H < <(magick identify -format "%w %h" "$src")
  out="${src%.png}_framed.png"

  magick -size "${W}x${H}" "gradient:${GRADIENT_FROM}-${GRADIENT_TO}" \
    \( "$src" -resize "$((W - PAD * 2))x" \) -gravity south -geometry +0+${PAD} -composite \
    -gravity north -pointsize 64 -fill white -font "$FONT" \
    -annotate +0+${PAD} "$caption" \
    "$out"
  echo "framed: $out"
done
