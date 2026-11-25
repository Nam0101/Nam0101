#!/usr/bin/env bash
# Regenerate assets/{hero,code,orbit,footer}.svg.
#
# Needs bun, python3 and a clone of Nam0101/claude-multiverse at $MULTIVERSE
# (default ~/.claude/skills/multiverse). Icons in tools/icons come from skillicons.dev (theme=dark).
# The universe ids below must match HERO_WORLDS and the about/orbit/footer worlds in gen.py.
#
# Preview one frame: python3 -I tools/shoot.py "$PWD/assets/hero.svg" "$PWD/shot" 850 354 2 7 12
# (headless Chrome does not run SMIL inside <img>; check scene switching in a real browser).
set -euo pipefail
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
worlds="$tmp/worlds.json"

bun tools/export.ts "$worlds" \
  neon-2099 dragonfire black-hole sky-whales synthwave-highway polar-night cherry-blossom deep \
  hologram-city void-drift golden-hour:done
python3 -I tools/gen.py assets tools/icons "$worlds"
