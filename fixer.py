#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fixer_v5.py — اضافه کردن متدهای حذف‌شده که هنوز استفاده می‌شن
- Draw.radial()
- Draw.shadow()
- UiButton.ICON_GEAR / ICON_NONE
"""
import sys
from pathlib import Path


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "src" / "main" / "java").is_dir():
            return p
    if (Path.cwd() / "src" / "main" / "java").is_dir():
        return Path.cwd()
    sys.exit("Project root not found.")


ROOT = find_root()
UI = ROOT / "src" / "main" / "java" / "com" / "oryvex" / "kbclient" / "ui"


# ===========================================================================
# 1) Draw.java — اضافه کردن radial() و shadow() قبل از بسته‌شدن کلاس
# ===========================================================================
DRAW = UI / "Draw.java"
txt = DRAW.read_text(encoding="utf-8")

# radial — نسخه ساده که فقط دایره می‌کشه (کافیه برای aurora blobs)
radial_method = '''
    /** Radial gradient approximation: soft circle fading to transparent. */
    public static void radial(float cx, float cy, float r, int color, boolean fill) {
        if (((color >>> 24) & 255) <= 4) return;
        int steps = Math.max(3, (int) r / 4);
        for (int i = steps; i >= 1; i--) {
            float t = i / (float) steps;
            float rr = r * t;
            int a = (int) (((color >>> 24) & 255) * (1f - t) * 0.5f);
            if (a <= 0) continue;
            circle(cx, cy, rr, (a << 24) | (color & 0xFFFFFF));
        }
        circle(cx, cy, r, color);
    }

    /** Soft drop shadow behind a rounded rect. */
    public static void shadow(float x, float y, float w, float h, float r, int color, float spread) {
        if (((color >>> 24) & 255) <= 4) return;
        for (int i = 1; i <= (int) spread; i++) {
            int a = (int) (((color >>> 24) & 255) * (1f - i / spread) * 0.10f);
            if (a <= 0) continue;
            roundRect(x - i, y - i + 1f, w + i * 2f, h + i * 2f, r + i,
                      (a << 24) | (color & 0xFFFFFF));
        }
    }
'''

# درست قبل از آخرین آکولاد کلاس اضافه کن
idx = txt.rfind("}")
if idx > 0:
    txt = txt[:idx] + radial_method + "\n}\n"
    DRAW.write_text(txt, encoding="utf-8")
    print(f"  [PATCH] {DRAW.relative_to(ROOT)}  (+radial +shadow)")
else:
    print("  [FAIL ] could not find closing brace in Draw.java")


# ===========================================================================
# 2) UiButton.java — اضافه کردن ICON_GEAR / ICON_NONE به عنوان alias
# ===========================================================================
BTN = UI / "UiButton.java"
txt = BTN.read_text(encoding="utf-8")

alias_block = '''    // Legacy aliases — older code references UiButton.ICON_* directly
    public static final int ICON_NONE = Draw.ICON_NONE;
    public static final int ICON_GEAR = Draw.ICON_GEAR;
'''

anchor = "    public int style = NORMAL;"
if "public static final int ICON_GEAR" not in txt:
    txt = txt.replace(anchor, alias_block + "\n" + anchor, 1)
    BTN.write_text(txt, encoding="utf-8")
    print(f"  [PATCH] {BTN.relative_to(ROOT)}  (+ICON_GEAR alias)")
else:
    print(f"  [SKIP ] {BTN.relative_to(ROOT)}")


# ===========================================================================
# 3) مطمئن شو Background.java و GuiAltManager.java هنوز همون امضاها رو صدا می‌زنن
# ===========================================================================
BG = UI / "Background.java"
if BG.exists():
    t = BG.read_text(encoding="utf-8")
    if "Draw.radial(" in t:
        print(f"  [ OK  ] Background.radial caller still matches")
    else:
        print(f"  [INFO ] Background no longer uses radial")

ALT = UI / "GuiAltManager.java"
if ALT.exists():
    t = ALT.read_text(encoding="utf-8")
    if "Draw.shadow(" in t:
        print(f"  [ OK  ] GuiAltManager.shadow caller still matches")
    else:
        print(f"  [INFO ] GuiAltManager no longer uses shadow")

MOD = ROOT / "src" / "main" / "java" / "com" / "oryvex" / "kbclient" / "KBClientMod.java"
if MOD.exists():
    t = MOD.read_text(encoding="utf-8")
    if "UiButton.ICON_GEAR" in t:
        print(f"  [ OK  ] KBClientMod references UiButton.ICON_GEAR — alias added")


print()
print("Done. Rebuild:  ./gradlew clean build")