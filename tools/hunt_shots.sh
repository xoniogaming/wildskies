#!/bin/sh
# Proposal shots (tools/hudshots/HuntShots.java): sh tools/hunt_shots.sh <out> <resource dir or -> <tag> <key> <offsets...>
# A resource dir given first on the classpath overrides catalog.json (a test catalog; src is untouched).
set -e
cd "$(dirname "$0")/.."
JH="${JAVA_HOME:-/c/Program Files/Eclipse Adoptium/jdk-21.0.12.101-hotspot}"
G="$HOME/.gradle/caches/modules-2/files-2.1"
CP="build/moddev/artifacts/neoforge-21.1.252-merged.jar;build/moddev/artifacts/neoforge-21.1.252-client-extra-aka-minecraft-resources.jar"
CP="$CP;$(tr -d '\r' < build/moddev/serverLegacyClasspath.txt | tr '\n' ';')"
for j in $(find "$G/org.lwjgl" -name "*3.3.3*.jar"); do CP="$CP;$(cygpath -w "$j")"; done
for j in $(find "$G/com.mojang" "$G/com.ibm.icu" -name "*.jar" | grep -E "blaze3d|text2speech|jtracy|icu4j"); do CP="$CP;$(cygpath -w "$j")"; done
if [ ! -f build/huntshots/HuntShots.class ] || [ tools/hudshots/HuntShots.java -nt build/huntshots/HuntShots.class ]; then
  rm -rf build/huntshots && mkdir -p build/huntshots
  "$JH/bin/javac" -proc:none -nowarn -XDignore.symbol.file -encoding UTF-8 -cp "$CP" -sourcepath src/main/java \
      -implicit:class -d build/huntshots tools/hudshots/*.java 2>&1 | grep -v "^Note:\|Unsafe\|^\s*\^\|^import sun\|warning" || true
fi
OUT="$1"; RES="$2"; shift 2
PRE=""; [ "$RES" != "-" ] && PRE="$RES;"
"$JH/bin/java" -cp "${PRE}build/huntshots;src/main/resources;$CP" HuntShots "$OUT" "$@" 2>&1 | grep -v "^\[LWJGL\]\|Incorrect key"
