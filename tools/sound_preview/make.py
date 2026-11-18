"""Listening previews for the sound pass (no mod files touched): python tools/sound_preview/make.py

Decodes the vanilla sounds named below from the launcher's asset store (tools/sound_preview/OggToWav.java, LWJGL's
stb_vorbis) and plays each option the way the mod would: Minecraft's pitch is playback speed, so a sound at pitch p
is resampled to 1/p of its length. Writes previews/sounds/<slot>_<letter>.wav.
"""
import json, os, subprocess, wave, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = pathlib.Path(os.environ["APPDATA"]) / ".minecraft/assets"
RAW = ROOT / "build/sounds_raw"
OUT = ROOT / "previews/sounds"
JH = r"C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot\bin"
G = pathlib.Path.home() / ".gradle/caches/modules-2/files-2.1/org.lwjgl"
SR = 44100

# each part: (vanilla sound, pitch, volume, start seconds)
ZOOM_SEQ = [(0.0, 1.5), (0.7, 1.5), (1.4, 1.5), (2.4, 1.2), (3.1, 1.2)]      # three steps in, two out (the code's x pitch)
ZOOM = {
    "A_now": [("item/spyglass/use", 1.4, 0.8)],
    "B_ratchet": [("item/crossbow/loading_end", 1.15, 0.7)],
    "C_click_then_blades": [("random/click", 1.2, 0.35), ("item/spyglass/use", 1.1, 0.5, 0.03)],
    "D_heavy_brass": [("block/crafter/craft", 1.0, 0.7)],
    "E_shutter": [("block/vault/open_shutter", 1.2, 0.6)],
}
FOUND_CHIME = [("block/amethyst/shimmer", 1.0, 0.9, 0.0)]                    # what "found" plays today
STAMP = {
    "A_pot_thud": [("block/decorated_pot/insert1", 0.8, 1.0)],
    "B_book_slot": [("block/chiseled_bookshelf/insert1", 0.8, 1.0)],
    "C_anvil_tap": [("block/smithing_table/smithing_table1", 1.3, 0.7)],
    "D_lodestone": [("block/lodestone/place1", 1.4, 0.9)],
    "E_leather_press": [("item/armor/equip_leather1", 0.7, 1.0), ("random/wood_click", 0.8, 0.6, 0.05)],
}


def decode(names):
    idx = json.load(open(ASSETS / "indexes/19.json"))["objects"]
    RAW.mkdir(parents=True, exist_ok=True)
    args = []
    for n in names:
        h = idx["minecraft/sounds/" + n + ".ogg"]["hash"]
        dst = RAW / (n.replace("/", "_") + ".wav")
        if not dst.exists():
            args += [str(ASSETS / "objects" / h[:2] / h), str(dst)]
    if args:
        jars = [str(p) for p in G.rglob("*.jar") if "3.3.3" in p.name and ("/lwjgl/" in p.as_posix() or "lwjgl-stb" in p.name)
                and ("natives" not in p.name or p.name.endswith("natives-windows.jar"))]
        cp = ";".join([str(RAW)] + jars)
        subprocess.run([JH + r"\javac", "-d", str(RAW), "-cp", cp, str(ROOT / "tools/sound_preview/OggToWav.java")], check=True)
        subprocess.run([JH + r"\java", "-cp", cp, "OggToWav", *args], check=True)


def load(n):
    with wave.open(str(RAW / (n.replace("/", "_") + ".wav"))) as w:
        r = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
    t = np.arange(0, len(x) * SR / r) * r / SR
    return np.interp(t, np.arange(len(x)), x)


def at_pitch(n, p):
    x = load(n)
    return np.interp(np.arange(0, len(x) - 1, p), np.arange(len(x)), x)


def mix(events, length):
    out = np.zeros(int(length * SR) + 1)
    for n, p, v, t in events:
        s = at_pitch(n, p) * v
        i = int(t * SR)
        s = s[: len(out) - i]
        out[i:i + len(s)] += s
    return out


def save(name, x):
    x = x / np.abs(x).max() * 0.9          # loudness evened out for listening; in game the volumes above apply
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / (name + ".wav")), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def parts(opt):
    return [(q[0], q[1], q[2], q[3] if len(q) > 3 else 0.0) for q in opt]


def main():
    names = {q[0] for d in (ZOOM, STAMP) for o in d.values() for q in o} | {q[0] for q in FOUND_CHIME}
    decode(sorted(names))
    for k, opt in ZOOM.items():
        ev = [(n, p * mul, v, t0 + t) for t0, mul in ZOOM_SEQ for n, p, v, t in parts(opt)]
        save("zoom_" + k, mix(ev, 4.2))
    for k, opt in STAMP.items():
        ev = FOUND_CHIME + [(n, p, v, 0.55 + t) for n, p, v, t in parts(opt)]
        save("stamp_" + k, mix(ev, 3.0))
    print("\n".join(sorted(p.name for p in OUT.glob("*.wav"))))


if __name__ == "__main__":
    main()
