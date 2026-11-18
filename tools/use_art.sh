#!/bin/sh
# Copies one art set into the mod's resources, for before/after comparisons:
#   sh tools/use_art.sh original|redesign
# A set is art/<set>/textures/** (same layout as assets/wildskies/textures), optionally SkySprites.java (the sprite
# table that matches its gui textures) and models/telescope_*.json. art/original is the backup of everything as it
# was on 2026-11-12, before the redesign. The set now in src/ is named in art/.in_use.
set -e
cd "$(dirname "$0")/.."
SET="$1"
[ -n "$SET" ] && [ -d "art/$SET/textures" ] || { echo "usage: sh tools/use_art.sh <set>  (sets: $(ls art | tr '\n' ' '))" >&2; exit 2; }
cp -r "art/$SET/textures/." src/main/resources/assets/wildskies/textures/
[ -f "art/$SET/SkySprites.java" ] && cp "art/$SET/SkySprites.java" src/main/java/wildskies/client/SkySprites.java
if [ -d "art/$SET/models" ]; then cp art/$SET/models/*.json src/main/resources/assets/wildskies/models/block/; fi
echo "$SET" > art/.in_use
echo "src/ now holds the '$SET' art set"
