#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_inter.py — دانلود Inter از منابع جدید"""
import io, os, sys, zipfile, urllib.request
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
FONTS_DIR = ROOT / "src" / "main" / "resources" / "fonts"
FONTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET = FONTS_DIR / "Inter-Regular.ttf"
if TARGET.exists() and TARGET.stat().st_size > 10_000:
    print(f"  [ OK  ] Inter-Regular.ttf already present")
    sys.exit(0)


def download(url: str) -> bytes:
    print(f"  [GET  ] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def save_from_zip(data: bytes):
    zf = zipfile.ZipFile(io.BytesIO(data))
    # اولویت: دقیقا Inter-Regular.ttf
    for name in zf.namelist():
        if os.path.basename(name).lower() == "inter-regular.ttf":
            TARGET.write_bytes(zf.read(name))
            return True
    # بعد: هر ttf که regular داره
    for name in zf.namelist():
        b = os.path.basename(name).lower()
        if b.endswith(".ttf") and "regular" in b:
            TARGET.write_bytes(zf.read(name))
            return True
    return False


# ---------------------------------------------------------------------------
# منابع به‌ترتیب اولویت — همه از CDN های پایداری که واقعا کار می‌کنن
# ---------------------------------------------------------------------------
ZIP_URLS = [
    # release رسمی Inter 4.1
    "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip",
    "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip",
    "https://github.com/rsms/inter/releases/download/v3.19/Inter-3.19.zip",
]

# فایل‌های مستقیم ttf از CDN های عمومی
DIRECT_URLS = [
    # jsDelivr روی مخزن rsms/inter (شاخه main)
    "https://cdn.jsdelivr.net/gh/rsms/inter@main/docs/font-files/Inter-Regular.ttf",
    "https://cdn.jsdelivr.net/gh/rsms/inter@v4.0/docs/font-files/Inter-Regular.ttf",
    # Google Fonts mirror (variable font — کار می‌کنه چون ttf معتبره)
    "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/inter/Inter%5Bopsz,wght%5D.ttf",
    # منبع جایگزین: fontsource روی jsDelivr
    "https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.16/files/inter-latin-400-normal.woff",
]

ok = False

print("[fix_inter] دانلود Inter ...")

# ---- ۱) zip ها ----
for url in ZIP_URLS:
    try:
        data = download(url)
        if save_from_zip(data):
            print(f"  [ OK  ] fonts/Inter-Regular.ttf  ({TARGET.stat().st_size} bytes)")
            ok = True
            break
    except Exception as e:
        print(f"         zip failed: {type(e).__name__}: {e}")

# ---- ۲) ttf های مستقیم ----
if not ok:
    for url in DIRECT_URLS:
        try:
            data = download(url)
            # اگر پسوند ttf داره یا حجم منطقیه، مستقیم ذخیره کن
            if len(data) > 20_000:
                TARGET.write_bytes(data)
                print(f"  [ OK  ] fonts/Inter-Regular.ttf  ({TARGET.stat().st_size} bytes)")
                ok = True
                break
        except Exception as e:
            print(f"         direct failed: {type(e).__name__}: {e}")


if not ok:
    print()
    print("  [WARN ] Inter دانلود نشد.")
    print("          ModernFontRenderer خودش به SansSerif fallback می‌کنه — مشکلی پیش نمیاد.")
    print("          ولی اگه Inter واقعی می‌خوای، از این لینک دستی دانلود کن:")
    print("             https://rsms.me/inter/")
    print(f"          و فایل Inter-Regular.ttf رو بذار در:")
    print(f"             {FONTS_DIR}")
    sys.exit(0)

print()
print("  Done. حالا:  .\\gradlew clean build")