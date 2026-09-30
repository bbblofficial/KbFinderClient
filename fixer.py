#!/usr/bin/env python3
"""
KB Client - Discord Rich Presence fixer
=======================================

What this fixes:

  1. startTimestamp is emitted in SECONDS. Discord silently drops
     millisecond timestamps, which is why your activity never shows
     in your Discord profile.

  2. Art assets (large_image / small_image) are behind an ENABLE_ASSETS
     flag so the activity still shows as text-only while you haven't
     uploaded the PNGs yet. If the asset keys don't exist in the
     Developer Portal, Discord strips them - and on some client builds
     drops the entire activity.

  3. DiscordRPC.start() is guaranteed to be wired into KBClientMod.init()
     and DiscordRPC.stop() into a JVM shutdown hook.

  4. Writes oryvex.png and minecraft.png (512x512) into ./discord_assets/
     so you can drag-and-drop them into the Developer Portal.

  5. Opens the Rich Presence -> Art Assets page for your APP_ID.

Usage
-----
    python fixer.py             apply everything, open the portal
    python fixer.py --dry-run   show what would change
    python fixer.py --no-open   don't launch the browser
    python fixer.py --restore   restore the newest backup
"""

import argparse
import datetime as dt
import re
import shutil
import struct
import sys
import webbrowser
import zlib
from pathlib import Path

APP_ID = "1554952903758716989"
PORTAL_ASSETS = f"https://discord.com/developers/applications/{APP_ID}/rich-presence/assets"
TAG = "[KB-FIXER-2]"


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------

def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "src" / "main" / "java" / "com" / "oryvex" / "kbclient").is_dir():
            return p
    # script was dropped inside the package itself
    if (here / "DiscordRPC.java").exists() or (here / "KBClientMod.java").exists():
        return here.parents[5]
    raise SystemExit(
        "Could not find src/main/java/com/oryvex/kbclient.\n"
        "Run fixer.py from the folder that contains 'src'."
    )


def kbpkg(root: Path) -> Path:
    return root / "src" / "main" / "java" / "com" / "oryvex" / "kbclient"


# ---------------------------------------------------------------------------
# backup / restore
# ---------------------------------------------------------------------------

def backup(root: Path, files):
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = root / ".fixer_backup" / stamp
    n = 0
    for f in files:
        if not f.exists():
            continue
        rel = f.relative_to(root)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        n += 1
    if n:
        print(f"  backed up {n} file(s) -> {dst.relative_to(root)}")
    return dst


def restore_latest(root: Path) -> int:
    base = root / ".fixer_backup"
    if not base.is_dir():
        print("No .fixer_backup folder found.")
        return 1
    snaps = sorted([p for p in base.iterdir() if p.is_dir()], reverse=True)
    if not snaps:
        print("No backups found.")
        return 1
    snap = snaps[0]
    n = 0
    for src in snap.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(snap)
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  restored {rel}")
        n += 1
    print(f"Restored {n} file(s) from {snap.name}.")
    return 0


# ---------------------------------------------------------------------------
# Java patching
# ---------------------------------------------------------------------------

def patch_discordrpc(path: Path, dry: bool) -> bool:
    if not path.exists():
        print(f"  ! {path.name} not found -- skipping")
        return False
    text = path.read_text(encoding="utf-8")
    if TAG in text:
        print(f"  = {path.name} already patched")
        return False

    out = text
    changed = False

    # -- 1. seconds, not milliseconds ---------------------------------------
    if re.search(r"startTime\s*=\s*System\.currentTimeMillis\(\)\s*;", out):
        out = re.sub(
            r"startTime\s*=\s*System\.currentTimeMillis\(\)\s*;",
            "startTime = System.currentTimeMillis() / 1000L; // "
            + TAG + " - SECONDS not ms",
            out, count=1,
        )
        changed = True

    # -- 2. ENABLE_ASSETS flag ---------------------------------------------
    if "ENABLE_ASSETS" not in out:
        out = re.sub(
            r'(private\s+static\s+final\s+String\s+APP_ID\s*=\s*"[^"]*"\s*;)',
            r"\1\n\n"
            "    // " + TAG + "\n"
            "    // Flip to true ONLY after uploading oryvex.png and minecraft.png\n"
            "    // under Discord Developer Portal -> Rich Presence -> Art Assets.\n"
            "    // Until the assets exist, Discord strips the keys (and on some\n"
            "    // client builds drops the whole activity), so we default to false.\n"
            "    private static final boolean ENABLE_ASSETS = false;",
            out, count=1,
        )
        changed = True

    # -- 3. gate the image assignments behind the flag ----------------------
    if "ENABLE_ASSETS" in out and "if (ENABLE_ASSETS)" not in out:
        m = re.search(
            r"([ \t]*presence\.largeImageKey\s*=[^\n]*\n"
            r"[ \t]*presence\.largeImageText\s*=[^\n]*\n"
            r"[ \t]*presence\.smallImageKey\s*=[^\n]*\n"
            r"[ \t]*presence\.smallImageText\s*=[^\n]*\n?)",
            out,
        )
        if m:
            block = m.group(1)
            indented = "".join(
                ("    " + ln) if ln.strip() else ln
                for ln in block.splitlines(True)
            )
            replacement = "if (ENABLE_ASSETS) { // " + TAG + "\n" + indented + "}\n"
            out = out[:m.start(1)] + replacement + out[m.end(1):]
            changed = True

    if not changed:
        print(f"  = {path.name}: nothing to change")
        return False
    if not dry:
        path.write_text(out, encoding="utf-8")
    print(f"  + patched {path.name}")
    return True


def patch_kbclientmod(path: Path, dry: bool) -> bool:
    if not path.exists():
        print(f"  ! {path.name} not found -- skipping")
        return False
    text = path.read_text(encoding="utf-8")
    if TAG in text:
        print(f"  = {path.name} already patched")
        return False

    out = text
    changed = False

    start_snippet = (
        "\n        try { DiscordRPC.start(); }\n"
        "        catch (Throwable t) { logger.warn(\"[KBClient] Discord RPC failed: \" + t); }"
        " // " + TAG
    )

    # -- 1. DiscordRPC.start() ---------------------------------------------
    if "DiscordRPC.start()" not in out:
        for pat in (
            re.compile(r"(installLoading\(\)\s*;)"),
            re.compile(r"(MinecraftForge\.EVENT_BUS\.register\(this\)\s*;)"),
        ):
            if pat.search(out):
                out = pat.sub(lambda m: m.group(1) + start_snippet, out, count=1)
                changed = True
                break

    # -- 2. shutdown hook ---------------------------------------------------
    if "addShutdownHook" not in out:
        pat = re.compile(r"(instance\s*=\s*this\s*;)")
        if pat.search(out):
            hook = (
                "\n        try {\n"
                "            Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {\n"
                "                @Override public void run() {\n"
                "                    try { DiscordRPC.stop(); } catch (Throwable ignored) {}\n"
                "                }\n"
                "            }, \"KBClient-RPC-Shutdown\"));\n"
                "        } catch (Throwable ignored) {} // " + TAG
            )
            out = pat.sub(lambda m: m.group(1) + hook, out, count=1)
            changed = True

    if not changed:
        print(f"  = {path.name}: nothing to change")
        return False
    if not dry:
        path.write_text(out, encoding="utf-8")
    print(f"  + patched {path.name}")
    return True


# ---------------------------------------------------------------------------
# PNG generation (no external deps)
# ---------------------------------------------------------------------------

def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _write_png(path: Path, w: int, h: int, rows):
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    path.write_bytes(
        sig
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )


def _radial(size, inner, outer, ring=None):
    cx = cy = (size - 1) / 2.0
    r = size * 0.48
    ir, ig, ib = inner
    orr, og, ob = outer
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = (dx * dx + dy * dy) ** 0.5
            if d > r:
                row += b"\x00\x00\x00\x00"
                continue
            t = d / r
            if ring and d > r * 0.9:
                rr, gg, bb = ring
            else:
                rr = int(ir + (orr - ir) * t)
                gg = int(ig + (og - ig) * t)
                bb = int(ib + (ob - ib) * t)
            row += bytes((rr, gg, bb, 255))
        rows.append(row)
    return rows


def make_assets(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    size = 512

    # oryvex -> cyan->indigo with a violet rim
    _write_png(out_dir / "oryvex.png", size, size,
               _radial(size, (34, 211, 238), (30, 64, 175),
                       ring=(167, 139, 250)))

    # minecraft -> grass green with a dirt rim
    _write_png(out_dir / "minecraft.png", size, size,
               _radial(size, (52, 211, 153), (21, 128, 61),
                       ring=(120, 53, 15)))

    print(f"  + wrote {out_dir / 'oryvex.png'}")
    print(f"  + wrote {out_dir / 'minecraft.png'}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="KB Client Discord RPC fixer")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would change, don't write")
    ap.add_argument("--no-open", action="store_true",
                    help="don't open the Discord Developer Portal")
    ap.add_argument("--restore", action="store_true",
                    help="restore the newest backup and exit")
    args = ap.parse_args()

    try:
        root = find_root()
    except SystemExit as e:
        print(e)
        return 1

    pkg = kbpkg(root)
    print(f"KB Client root : {root}")
    print(f"Package dir    : {pkg}")
    print()

    if args.restore:
        return restore_latest(root)

    rpc = pkg / "DiscordRPC.java"
    main_mod = pkg / "KBClientMod.java"

    if not args.dry_run:
        backup(root, [rpc, main_mod])

    print("Patching Java sources...")
    patch_discordrpc(rpc, args.dry_run)
    patch_kbclientmod(main_mod, args.dry_run)

    print()
    print("Generating Discord Rich Presence art assets...")
    assets_dir = root / "discord_assets"
    if args.dry_run:
        print(f"  (dry-run) would write {assets_dir}/oryvex.png, minecraft.png")
    else:
        make_assets(assets_dir)

    print()
    print("=" * 70)
    print("  NEXT STEPS  --  show the emoji / asset in the Discord portal")
    print("=" * 70)
    print()
    print("  1. Open the Rich Presence -> Art Assets page:")
    print(f"       {PORTAL_ASSETS}")
    print()
    print("  2. Click 'Add Image(s)' and drag BOTH files in:")
    print(f"       {assets_dir / 'oryvex.png'}")
    print(f"       {assets_dir / 'minecraft.png'}")
    print()
    print("     The asset KEY is the filename without '.png'. It must be")
    print("     exactly  'oryvex'  and  'minecraft'  (lowercase).")
    print("     If the key is wrong Discord will strip it from the presence.")
    print()
    print("  3. Wait 1-5 minutes for Discord's CDN to propagate the assets.")
    print()
    print("  4. In  src/main/java/com/oryvex/kbclient/DiscordRPC.java")
    print("     change:   private static final boolean ENABLE_ASSETS = false;")
    print("     to:       private static final boolean ENABLE_ASSETS = true;")
    print()
    print("  5. In the Discord desktop client, enable:")
    print("       User Settings  ->  Activity Privacy")
    print("         ->  'Display current activity as a status message' = ON")
    print()
    print("  6. Rebuild the mod. Launch Discord BEFORE Minecraft so the")
    print("     \\\\.\\pipe\\discord-ipc-0 pipe exists when the mod starts.")
    print()
    print("=" * 70)

    if not args.no_open:
        try:
            webbrowser.open(PORTAL_ASSETS)
            print(f"  (opened {PORTAL_ASSETS})")
        except Exception as e:
            print(f"  (could not open browser: {e})")

    return 0


if __name__ == "__main__":
    sys.exit(main())