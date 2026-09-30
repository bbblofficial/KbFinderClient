#!/usr/bin/env python3
"""
fixer.py - fixes the "black screen after Singleplayer -> Back" bug in the
KBClient / Knockback Finder mod (Forge 1.8.9) and adds safety changes.

Usage (run from the project root, e.g. ...\\KnockbackClientMod):
    python fixer.py                 # auto-detect project in current folder
    python fixer.py "C:\\path\\to\\KnockbackClientMod"
    python fixer.py --dry-run       # show what would change, write nothing
    python fixer.py --commit        # git commit after patching
    python fixer.py --restore       # restore the latest backup

What it does
  1. Backs up all .java files  -> .fixer_backup/<timestamp>/
  2. Adds GlSafe.java          -> save/restore/reset OpenGL state
  3. Adds GuiStateFixer.java   -> if screen becomes null with no world, opens
                                  GuiMainMenu (this is what causes black screen)
  4. Registers GuiStateFixer in your @Mod class (init / preInit)
  5. Wraps render methods of *Loading* classes with push/try/finally/pop GL
  6. Reports suspicious code (displayGuiScreen(null), event.gui = null ...)
  7. Writes FIXER_CHANGES.md
Re-running is safe (idempotent).
"""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

MARK = "GlSafe"
BACKUP_DIR = ".fixer_backup"

GLSAFE = """package %PKG%;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.GlStateManager;
import org.lwjgl.opengl.GL11;

/** Added by fixer.py - keeps OpenGL state sane so the screen never stays black. */
public final class GlSafe {
    private GlSafe() {}

    public static void push() {
        try { GL11.glPushAttrib(GL11.GL_ALL_ATTRIB_BITS); } catch (Throwable ignored) {}
    }

    public static void pop() {
        try { GL11.glPopAttrib(); } catch (Throwable ignored) {}
        reset();
    }

    public static void reset() {
        try {
            Minecraft mc = Minecraft.getMinecraft();
            if (mc != null && mc.theWorld == null && mc.getFramebuffer() != null) {
                mc.getFramebuffer().bindFramebuffer(true);
            }
            GL11.glDisable(GL11.GL_SCISSOR_TEST);
            GlStateManager.colorMask(true, true, true, true);
            GlStateManager.enableTexture2D();
            GlStateManager.disableLighting();
            GlStateManager.enableAlpha();
            GlStateManager.enableBlend();
            GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
            GlStateManager.color(1.0F, 1.0F, 1.0F, 1.0F);
        } catch (Throwable ignored) {}
    }
}
"""

FIXER_CLASS = """package %PKG%;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiMainMenu;
import net.minecraftforge.client.event.GuiOpenEvent;
import net.minecraftforge.fml.common.eventhandler.EventPriority;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.gameevent.TickEvent;

/** Added by fixer.py - prevents the black screen when returning from Singleplayer. */
public class GuiStateFixer {
    private int blackTicks = 0;

    /** Runs last: if anything turned the next screen into null while no world is loaded, use the main menu. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public void onGuiOpen(GuiOpenEvent e) {
        Minecraft mc = Minecraft.getMinecraft();
        if (e.gui == null && mc.theWorld == null) {
            e.gui = new GuiMainMenu();
        }
        GlSafe.reset();
    }

    /** Safety net: no world + no screen for 3 ticks = black screen -> open the main menu. */
    @SubscribeEvent
    public void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.theWorld == null && mc.currentScreen == null) {
            if (++blackTicks >= 3) {
                blackTicks = 0;
                GlSafe.reset();
                mc.displayGuiScreen(new GuiMainMenu());
            }
        } else {
            blackTicks = 0;
        }
    }

    /** In menus, reset GL state at the end of each frame so a broken overlay can't blacken the screen. */
    @SubscribeEvent
    public void onRenderTick(TickEvent.RenderTickEvent e) {
        if (e.phase == TickEvent.Phase.END && Minecraft.getMinecraft().theWorld == null) {
            GlSafe.reset();
        }
    }
}
"""


# ----------------------------------------------------------------- helpers
def mask_java(s: str) -> str:
    """Replace comments/string/char contents with spaces (same length) so regex/brace scans are safe."""
    out = list(s)
    n = len(s)
    i = 0

    def blank(a, b):
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = s[i]
        if s.startswith("//", i):
            j = s.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(i, j)
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and s[j] != c:
                if s[j] == "\\":
                    j += 1
                j += 1
            blank(i + 1, j)
            i = j + 1
        else:
            i += 1
    return "".join(out)


def match_brace(masked: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(masked)):
        ch = masked[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def write(p: Path, text: str, dry: bool):
    if not dry:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")


# ----------------------------------------------------------------- steps
def find_sources(root: Path):
    skip = {".git", BACKUP_DIR, "build", ".gradle", "run", "bin", "out"}
    files = []
    for p in root.rglob("*.java"):
        if any(part in skip for part in p.parts):
            continue
        files.append(p)
    return files


def find_main(files):
    for p in files:
        t = read(p)
        if re.search(r"@Mod\s*\(", t) and "net.minecraftforge.fml.common.Mod" in t:
            m = re.search(r"^\s*package\s+([\w.]+)\s*;", t, re.M)
            return p, (m.group(1) if m else "")
    return None, ""


def backup(root: Path, files, dry):
    if dry:
        return None
    dest = root / BACKUP_DIR / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for p in files:
        target = dest / p.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    return dest


def register_fixer(main_file: Path, pkg: str, dry, log):
    text = read(main_file)
    if "GuiStateFixer" in text:
        log.append(f"[skip] GuiStateFixer already registered in {main_file.name}")
        return
    masked = mask_java(text)
    pat = re.compile(r"void\s+\w+\s*\(\s*(?:[\w.]*\.)?FML(Pre)?InitializationEvent\s+\w+\s*\)\s*(?:throws[\w\s.,]+)?\{")
    matches = list(pat.finditer(masked))
    if not matches:
        log.append(f"[WARN] No init/preInit method found in {main_file.name}. Add manually:\n"
                   f"       net.minecraftforge.common.MinecraftForge.EVENT_BUS.register(new {pkg}.GuiStateFixer());\n"
                   f"       net.minecraftforge.fml.common.FMLCommonHandler.instance().bus().register(new {pkg}.GuiStateFixer());")
        return
    m = next((x for x in matches if not x.group(1)), matches[0])
    fq = f"{pkg}.GuiStateFixer" if pkg else "GuiStateFixer"
    inject = (f"\n        {fq} __fix = new {fq}();"
              f"\n        net.minecraftforge.common.MinecraftForge.EVENT_BUS.register(__fix);"
              f"\n        net.minecraftforge.fml.common.FMLCommonHandler.instance().bus().register(__fix);")
    text = text[:m.end()] + inject + text[m.end():]
    write(main_file, text, dry)
    log.append(f"[ok]   Registered GuiStateFixer in {main_file.name}")


SIG = re.compile(
    r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?void\s+(\w+)\s*\([^)]*\)\s*(?:throws[\w\s.,]+)?\{")
SKIP_NAMES = re.compile(r"^(get|is|set(?!Loading)|init|load$|register|equals|hashCode|toString)", re.I)


def wrap_loading_methods(p: Path, pkg: str, dry, log):
    text = read(p)
    if MARK + ".push" in text:
        log.append(f"[skip] {p.name} already wrapped")
        return
    masked = mask_java(text)
    chosen, last_end = [], -1
    for m in SIG.finditer(masked):
        if m.start() < last_end or SKIP_NAMES.match(m.group(1)):
            continue
        close = match_brace(masked, m.end() - 1)
        if close < 0:
            continue
        chosen.append((m.end() - 1, close, m.group(1)))
        last_end = close
    if not chosen:
        log.append(f"[info] {p.name}: no void methods to wrap")
        return
    fq = f"{pkg}.GlSafe" if pkg else "GlSafe"
    for open_i, close_i, _ in reversed(chosen):
        text = text[:close_i] + "} finally { " + fq + ".pop(); }\n    " + text[close_i:]
        text = text[:open_i + 1] + f"\n        {fq}.push(); try {{" + text[open_i + 1:]
    write(p, text, dry)
    log.append(f"[ok]   {p.name}: wrapped {len(chosen)} method(s): " + ", ".join(n for _, _, n in chosen))


SUSPECT = [
    (re.compile(r"displayGuiScreen\s*\(\s*null\s*\)"), "displayGuiScreen(null) - black screen if no world is loaded"),
    (re.compile(r"\.gui\s*=\s*null"), "GuiOpenEvent gui set to null"),
    (re.compile(r"GuiOpenEvent"), "GuiOpenEvent handler - check it never cancels/nulls the menu"),
    (re.compile(r"setLoadingScreen|loadingScreen\s*="), "loadingScreen replaced - make sure it is restored"),
    (re.compile(r"glColorMask\s*\(\s*false|glDisable\s*\(\s*GL11\.GL_TEXTURE_2D|glScissor|GL_SCISSOR_TEST"),
     "GL state change that may not be restored"),
]


def scan_suspects(files, root, log):
    found = False
    for p in files:
        if p.name in ("GlSafe.java", "GuiStateFixer.java"):
            continue
        masked = mask_java(read(p))
        for i, line in enumerate(masked.splitlines(), 1):
            for rx, why in SUSPECT:
                if rx.search(line):
                    if not found:
                        log.append("\n--- Suspicious code (review manually) ---")
                        found = True
                    log.append(f"  {p.relative_to(root)}:{i}: {why}\n      {line.strip()}")


def restore(root: Path):
    base = root / BACKUP_DIR
    if not base.exists():
        print("No backups found.")
        return
    latest = sorted(base.iterdir())[-1]
    for p in latest.rglob("*.java"):
        target = root / p.relative_to(latest)
        shutil.copy2(p, target)
    for name in ("GlSafe.java", "GuiStateFixer.java"):
        for p in root.rglob(name):
            if BACKUP_DIR not in p.parts:
                p.unlink()
    print(f"Restored from {latest}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--restore", action="store_true")
    a = ap.parse_args()
    root = Path(a.path).resolve()

    if a.restore:
        restore(root)
        return

    files = find_sources(root)
    if not files:
        print(f"No .java files found under {root}.\n"
              "Run this from the folder that contains src/main/java (your mod source), "
              "or pass the path as an argument.")
        sys.exit(1)

    main_file, pkg = find_main(files)
    if not main_file:
        print("Could not find the @Mod main class. Tell me the file name and I'll adjust.")
        sys.exit(1)

    log = [f"Project: {root}", f"Main class: {main_file.relative_to(root)}  (package: {pkg or '<default>'})"]
    b = backup(root, files, a.dry_run)
    if b:
        log.append(f"Backup: {b}")

    pkg_dir = main_file.parent
    for name, tpl in (("GlSafe.java", GLSAFE), ("GuiStateFixer.java", FIXER_CLASS)):
        write(pkg_dir / name, tpl.replace("%PKG%", pkg) if pkg else tpl.replace("package %PKG%;\n\n", ""), a.dry_run)
        log.append(f"[ok]   Wrote {name}")

    register_fixer(main_file, pkg, a.dry_run, log)

    loading = [p for p in files if "loading" in p.name.lower()
               or re.search(r"LoadingScreen", read(p))]
    loading = [p for p in loading if p.name not in ("GlSafe.java", "GuiStateFixer.java")]
    if loading:
        for p in loading:
            wrap_loading_methods(p, pkg, a.dry_run, log)
    else:
        log.append("[info] No loading-screen class found (nothing wrapped).")

    scan_suspects(find_sources(root), root, log)

    changes = (
        "# Fixer changes\n\n"
        f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n"
        "- Added `GlSafe` (OpenGL state push/pop/reset).\n"
        "- Added `GuiStateFixer`: opens GuiMainMenu if the screen is null with no world (fixes black screen after Singleplayer -> Back).\n"
        "- Registered `GuiStateFixer` in the main mod class.\n"
        "- Wrapped loading-screen render methods in GL push/pop with try/finally.\n"
    )
    write(root / "FIXER_CHANGES.md", changes, a.dry_run)

    print("\n".join(log))
    print("\nDone." + (" (dry-run, nothing written)" if a.dry_run else " Rebuild the mod (gradlew build) and test."))

    if a.commit and not a.dry_run:
        try:
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m",
                            "Fix black screen after leaving Singleplayer (GuiStateFixer + GlSafe)"],
                           cwd=root, check=True)
        except Exception as e:
            print(f"git commit failed: {e}")


if __name__ == "__main__":
    main()