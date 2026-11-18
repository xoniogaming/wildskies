#!/bin/sh
# Renders the star view and the Star Atlas with the real draw code (tools/hudshots/SkyShots.java):
#   sh tools/hud_shots.sh <out dir> [scene filter] [--small]
# Needs the dev environment set up once by gradle (build/moddev/artifacts, ~/.gradle caches).
set -e
cd "$(dirname "$0")/.."
JH="${JAVA_HOME:-/c/Program Files/Eclipse Adoptium/jdk-21.0.12.101-hotspot}"
G="$HOME/.gradle/caches/modules-2/files-2.1"
CP="build/moddev/artifacts/neoforge-21.1.252-merged.jar;build/moddev/artifacts/neoforge-21.1.252-client-extra-aka-minecraft-resources.jar"
CP="$CP;$(tr -d '\r' < build/moddev/serverLegacyClasspath.txt | tr '\n' ';')"
for j in $(find "$G/org.lwjgl" -name "*3.3.3*.jar"); do CP="$CP;$(cygpath -w "$j")"; done
for j in $(find "$G/maven.modrinth/8BmcQJ2H/Grwn5rUB" -name "*.jar"); do CP="$CP;$(cygpath -w "$j")"; done   # GeckoLib (telescope)
for j in $(find "$G/com.mojang" "$G/com.ibm.icu" -name "*.jar" | grep -E "blaze3d|text2speech|jtracy|icu4j"); do CP="$CP;$(cygpath -w "$j")"; done

rm -rf build/hudshots && mkdir -p build/hudshots
"$JH/bin/javac" -proc:none -nowarn -XDignore.symbol.file -encoding UTF-8 -cp "$CP" -sourcepath src/main/java \
    -implicit:class -d build/hudshots tools/hudshots/*.java 2>&1 | grep -v "^Note:\|Unsafe\|^\s*\^\|^import sun\|warning" || true
"$JH/bin/java" -cp "build/hudshots;src/main/resources;$CP" WarmShots "$@" 2>&1 | grep -v "^\[LWJGL\]\|Incorrect key"
