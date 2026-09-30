#!/usr/bin/env python3
"""
fix_blackscreen.py - real fix for the black screen after Singleplayer -> Back.

Root cause: FadeScreen.closing stays true after closeTo(...), so when the same
screen instance (GuiModernMenu) is shown again, drawFade() paints a fully opaque
black rect and all input is blocked.

Fix: reset the fade state every time the screen is (re)displayed.
Also removes the GlSafe push/pop wrappers that fixer.py added to KBLoading /
LoadingArt (raw glPushAttrib/glPopAttrib can desync GlStateManager's cache).

Run from the project root:   python fix_blackscreen.py
"""
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
ui = root / "src/main/java/com/oryvex/kbclient/ui"


def load(p):
    return p.read_bytes().decode("utf-8").replace("\r\n", "\n")


def save(p, text):
    shutil.copy2(p, str(p) + ".bak")
    p.write_bytes(text.encode("utf-8"))


# ---------------------------------------------------------------- FadeScreen
fs = ui / "FadeScreen.java"
if not fs.exists():
    sys.exit(f"Not found: {fs}\nRun this from the KnockbackClientMod folder.")

t = load(fs)
if "boolean finished" in t:
    print("[skip] FadeScreen already patched")
else:
    def rep(old, new):
        global t
        if old not in t:
            sys.exit(f"Pattern not found in FadeScreen.java:\n{old}")
        t = t.replace(old, new, 1)

    rep("private final long openedAt = System.currentTimeMillis();",
        "private long openedAt = System.currentTimeMillis();")
    rep("    private Runnable after;\n",
        "    private Runnable after;\n    private boolean finished;\n")
    rep("            after = null;\n            r.run();",
        "            after = null;\n            finished = true;\n            r.run();")
    rep("    public boolean isClosing() { return closing; }\n",
        "    public boolean isClosing() { return closing; }\n\n"
        "    /** Called every time this screen is displayed (also when a parent screen is re-opened via Back). */\n"
        "    @Override\n"
        "    public void setWorldAndResolution(Minecraft mc, int width, int height) {\n"
        "        if (finished) {          // was closed earlier -> start fresh (no black overlay, input enabled)\n"
        "            closing = false;\n"
        "            finished = false;\n"
        "            after = null;\n"
        "            openedAt = System.currentTimeMillis();\n"
        "        }\n"
        "        super.setWorldAndResolution(mc, width, height);\n"
        "    }\n")
    save(fs, t)
    print("[ok]   FadeScreen.java patched (backup: FadeScreen.java.bak)")

# ------------------------------------------------- remove GlSafe push/pop wrappers
OPEN = "com.oryvex.kbclient.GlSafe.push(); try {"
CLOSE = "} finally { com.oryvex.kbclient.GlSafe.pop(); }"
for name in ("KBLoading.java", "LoadingArt.java"):
    p = ui / name
    if not p.exists():
        continue
    s = load(p)
    if OPEN not in s:
        print(f"[skip] {name}: no wrappers")
        continue
    s = s.replace(OPEN, "").replace(CLOSE, "")
    save(p, s)
    print(f"[ok]   {name}: removed GlSafe wrappers (backup: {name}.bak)")

print("\nDone. Rebuild (gradlew build), copy the new jar to .minecraft\\mods, and test "
      "Singleplayer -> Back, Analyzer -> Back, Options -> Done.")