#!/usr/bin/env python3
"""
fixer.py — repairs the GitHub Actions build failure.

Error being fixed (from the CI log):

    GuiAnalyzer.java:294: error: cannot find symbol
        Draw.dashedH(px + 126, y0 + 11, 10, Theme.WARN);
        symbol:   method dashedH(int,int,int,int)
        location: class Draw

The rewritten Draw.java (float-based primitives) no longer ships the old
dashedH(int,int,int,int) helper, but GuiAnalyzer.java still calls it in the
header rule and in the Graph tab. This script re-adds a matching dashedH()
(plus a companion dashedV()) just before the closing brace of Draw.java, then
scans the entire kbclient package for any other Draw.<name>(...) calls that
have no matching declaration.

Usage:
    python fixer.py            # patch + audit
    python fixer.py --check    # audit only (no writes)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PKG  = ROOT / "src" / "main" / "java" / "com" / "oryvex" / "kbclient"
DRAW = PKG / "ui" / "Draw.java"


# Code injected just before the closing brace of the Draw class.
_INJECT = '''

    /* ------------------------------------------------------------------ */
    /*  Dashed rules (restored — the Graph tab and section headers use them) */
    /* ------------------------------------------------------------------ */

    /** Dashed horizontal rule from (x, y) with length w. */
    public static void dashedH(float x, float y, float w, int color) {
        if (w <= 0f || ((color >>> 24) & 255) <= 4) return;
        for (float i = 0f; i < w; i += 6f) {
            int x0 = (int) (x + i);
            int x1 = (int) (x + Math.min(w, i + 3f));
            Gui.drawRect(x0, (int) y, x1, (int) y + 1, color);
        }
    }

    /** Dashed vertical rule from (x, y) with length h. */
    public static void dashedV(float x, float y, float h, int color) {
        if (h <= 0f || ((color >>> 24) & 255) <= 4) return;
        for (float i = 0f; i < h; i += 6f) {
            int y0 = (int) (y + i);
            int y1 = (int) (y + Math.min(h, i + 3f));
            Gui.drawRect((int) x, y0, (int) x + 1, y1, color);
        }
    }
'''


def log(msg: str) -> None:
    print(f"[fixer] {msg}")


def patch(apply: bool = True) -> bool:
    if not DRAW.exists():
        log(f"!! Draw.java not found at {DRAW}")
        return False

    src = DRAW.read_text(encoding="utf-8")

    if re.search(r"\bvoid\s+dashedH\s*\(", src):
        log("Draw.dashedH already exists — nothing to patch.")
        return True

    log(f"missing Draw.dashedH in {DRAW.relative_to(ROOT)}")
    if not apply:
        return False

    # One-time backup.
    bak = DRAW.with_name(DRAW.name + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
        log(f"backup written -> {bak.relative_to(ROOT)}")

    # Insert just before the last `}` of the file (the class's closing brace).
    idx = src.rfind("}")
    if idx < 0:
        log("!! could not find the class's closing brace")
        return False

    DRAW.write_text(src[:idx] + _INJECT + src[idx:], encoding="utf-8")
    log("patched: added Draw.dashedH() and Draw.dashedV()")
    return True


def audit() -> int:
    """Report any Draw.<name>(...) call whose method isn't declared in Draw.java."""
    if not DRAW.exists():
        return 1

    src = DRAW.read_text(encoding="utf-8")
    # Match: `public static <type> <name>(`
    defined = set(re.findall(
        r"public\s+static\s+[\w.<>\[\],\s]+?\s+(\w+)\s*\(",
        src,
    ))

    missing: dict[str, set[str]] = {}
    for jf in PKG.rglob("*.java"):
        text = jf.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"\bDraw\.(\w+)\s*\(", text):
            if m.group(1) not in defined:
                missing.setdefault(m.group(1), set()).add(str(jf.relative_to(ROOT)))

    if not missing:
        log("audit OK — every Draw.* call resolves to a method on Draw.java.")
        return 0

    log("audit: unresolved Draw.* references found:")
    for name, files in sorted(missing.items()):
        log(f"    Draw.{name}  <-  {', '.join(sorted(files))}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Patch Draw.java with the missing dashedH() helper."
    )
    ap.add_argument("--check", action="store_true",
                    help="report only, do not write to disk")
    args = ap.parse_args()

    ok = patch(apply=not args.check)
    rc = audit()
    return 0 if (ok and rc == 0) else 1


if __name__ == "__main__":
    sys.exit(main())