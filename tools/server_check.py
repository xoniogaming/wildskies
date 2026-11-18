#!/usr/bin/env python3
"""
Server check + self-test for Wild Skies.
Server check + self-test for Wild Skies: starts the dev server (./gradlew runServer) with WILDSKIES_SELFTEST=1, makes a
world and waits for dev/SelfTest.java (catalog, find rules, Atlas, crater sites, carving, dawn, fading, a landing).
Fails on a crash, an error mentioning wildskies, or a "WILDSKIES FAIL" line.
"""
import os
import pathlib
import re
import signal
import subprocess
import sys
import time

TIMEOUT_SECONDS = 35 * 60
FATAL = re.compile(
    r"Feature order cycle|---- Minecraft Crash Report ----|Failed to start the minecraft server|"
    r"Encountered an unexpected exception|Failed to load registries|ModLoadingException|Mod loading has failed")
DATA_ERROR = re.compile(r"Unknown registry key|Errors in element|Failed to parse|Couldn't parse|Couldn't load tag|DataPack.*failed|Missing model|Unable to load model")
DONE = re.compile(r"Done \(\d+[.,]\d+s\)! For help")
FINISHED = "WILDSKIES finished"
REQUIRED = []

run = pathlib.Path("run")
run.mkdir(exist_ok=True)
(run / "eula.txt").write_text("eula=true\n")
(run / "wildskies-selftest").write_text("created by tools/server_check.py: enables the Wild Skies self-test\n")
# max-tick-time=-1: the self-test runs for a while on the server thread, so the watchdog must not kill it.
(run / "server.properties").write_text("online-mode=false\nlevel-seed=wildskies\nspawn-protection=0\nmax-tick-time=-1\n")

env = dict(os.environ, WILDSKIES_SELFTEST="1")
log_path = pathlib.Path("server-check.log")
WINDOWS = os.name == "nt"


def stop(proc: subprocess.Popen) -> None:
    """Stops Gradle and the server it started (the whole process tree)."""
    if WINDOWS:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        proc.wait(timeout=60)
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=60)
    except Exception:
        os.killpg(proc.pid, signal.SIGKILL)


with log_path.open("w", encoding="utf-8") as log:
    gradle = [str(pathlib.Path("gradlew.bat").resolve())] if WINDOWS else ["./gradlew"]
    proc = subprocess.Popen(gradle + ["runServer", "--no-daemon", "--console=plain"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace", env=env,
                            **({} if WINDOWS else {"start_new_session": True}))
    start = time.time()
    result = None
    done = False
    enabled = False
    for line in proc.stdout:
        log.write(line)
        if FATAL.search(line) or (DATA_ERROR.search(line) and "wildskies" in line):
            print("FAILURE LINE:", line.rstrip())
            result = "failed"
        if "WILDSKIES" in line:
            print(line.rstrip()[line.find("WILDSKIES"):])
        if "WILDSKIES enabled" in line:
            enabled = True
        if DONE.search(line):
            done = True
            if not enabled:
                print("FAILURE: the server started but the self-test was not enabled (wildskies.selftest not set)")
                result = "failed"
        # A crash during world creation never reaches "Done", so stop at once instead of waiting for the timeout.
        if FINISHED in line or FATAL.search(line) or (result == "failed" and done):
            break
        if time.time() - start > TIMEOUT_SECONDS:
            result = "timeout"
            break
    stop(proc)

text = log_path.read_text(encoding="utf-8", errors="replace")
if result is None:
    result = "ok" if (done and FINISHED in text) else "failed"
if "WILDSKIES FAIL" in text:
    result = "failed"
for marker in REQUIRED:
    if marker not in text:
        print("MISSING REQUIRED LOG LINE:", marker)
        result = "failed"

tests = [l[l.find("WILDSKIES"):] for l in text.splitlines() if "WILDSKIES" in l]
summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a") as out:
        out.write("### Wild Skies self-test\n```\n" + "\n".join(tests) + "\n```\n")
for pattern in ("WARN", "ERROR"):
    hits = [l for l in text.splitlines() if pattern in l and re.search(r"(?i)wildskies|mixin|feature|registry|biome|tag|model", l)]
    print(f"--- {pattern} lines mentioning wildcasino/feature/registry/biome/tag/model: {len(hits)}")
    for l in hits[:80]:
        print(l[:400])
print("--- last 40 log lines")
print("\n".join(text.splitlines()[-40:]))
print("RESULT:", result)
sys.exit(0 if result == "ok" else 1)
