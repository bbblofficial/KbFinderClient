#!/usr/bin/env python3
"""
fixer.py - KB Client patch script (v1.0.0 pass)

Applies, in one run, from the project root (same folder as build.gradle):
  1. Fixes KB capture starting on its own on every join/connect - it now
     only starts when you actually run /findkb (or /kb start).
  2. Adds a "Reconnect" button to the Disconnected screen.
  3. Reduces UI motion to fade-in/fade-out only (drops the button slide-up
     entrance, the spinning gear icon, and the toast slide-in).
  4. Bumps the mod version to 1.0.0 everywhere it's hardcoded.
  5. Adds a "Created by muvixo" watermark (main menu, loading screen, HUD).
  6. Adds proguard-rules.pro and a ProGuard obfuscation step to the
     GitHub Actions build workflow.

Safe to re-run: each patch is skipped if it's already applied, and every
touched file is backed up first under .fixer_backup/<timestamp>/, same
layout as the source tree, with a manifest.txt (M = modified, C = created)
next to it - same convention the project's own adder.py backups use.
"""
import os
import sys
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "oryvex", "kbclient")


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# text patches: (relative_path, old, new, label)
# a patch is skipped if `new` is already present (idempotent),
# and reported as a mismatch if `old` can't be found (source drifted).
# ---------------------------------------------------------------------------
PATCHES = [
    # 1) KB capture must not start on its own
    (
        "src/main/java/com/oryvex/kbclient/KBTracker.java",
        "    private boolean recording = true;",
        "    private boolean recording = false;",
        "KBTracker: default recording state",
    ),
    (
        "src/main/java/com/oryvex/kbclient/KBTracker.java",
        "        server = name;\n        recording = true;\n        goal = 0;",
        "        server = name;\n        recording = false; // fixed: capture must be started explicitly with /findkb (or /kb start), it must not run on its own\n        goal = 0;",
        "KBTracker: onConnect no longer auto-starts recording",
    ),

    # 2) version bump
    (
        "src/main/java/com/oryvex/kbclient/KBClientMod.java",
        'public static final String VERSION = "3.0.0";',
        'public static final String VERSION = "1.0.0";',
        "KBClientMod: version -> 1.0.0",
    ),
    (
        "build.gradle",
        'version = "3.0.0"',
        'version = "1.0.0"',
        "build.gradle: version -> 1.0.0",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/GuiModernMenu.java",
        'Draw.text("KB Client 3.0", 6, this.height - 12, Theme.DIM, 0.8f, false);',
        'Draw.text("KB Client 1.0", 6, this.height - 12, Theme.DIM, 0.8f, false);',
        "GuiModernMenu: footer label -> 1.0",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/LoadingArt.java",
        'Draw.text("KB Client 3.0", 6, h - 12, Theme.DIM, 0.75f, false);',
        'Draw.text("KB Client 1.0", 6, h - 12, Theme.DIM, 0.75f, false);',
        "LoadingArt: footer label -> 1.0",
    ),

    # 3) reconnect button - imports, fields
    (
        "src/main/java/com/oryvex/kbclient/KBClientMod.java",
        "import net.minecraft.client.gui.GuiButton;\n"
        "import net.minecraft.client.gui.GuiChat;\n"
        "import net.minecraft.client.gui.GuiDownloadTerrain;\n"
        "import net.minecraft.client.gui.GuiIngameMenu;\n"
        "import net.minecraft.client.gui.GuiMainMenu;\n"
        "import net.minecraft.client.gui.GuiScreen;\n"
        "import net.minecraft.client.gui.inventory.GuiContainer;\n"
        "import net.minecraft.client.settings.KeyBinding;\n"
        "import net.minecraft.network.NetworkManager;",
        "import net.minecraft.client.gui.GuiButton;\n"
        "import net.minecraft.client.gui.GuiChat;\n"
        "import net.minecraft.client.gui.GuiDisconnected;\n"
        "import net.minecraft.client.gui.GuiDownloadTerrain;\n"
        "import net.minecraft.client.gui.GuiIngameMenu;\n"
        "import net.minecraft.client.gui.GuiMainMenu;\n"
        "import net.minecraft.client.gui.GuiScreen;\n"
        "import net.minecraft.client.gui.inventory.GuiContainer;\n"
        "import net.minecraft.client.multiplayer.GuiConnecting;\n"
        "import net.minecraft.client.multiplayer.ServerData;\n"
        "import net.minecraft.client.settings.KeyBinding;\n"
        "import net.minecraft.network.NetworkManager;",
        "KBClientMod: reconnect imports",
    ),
    (
        "src/main/java/com/oryvex/kbclient/KBClientMod.java",
        '    public static final String VERSION = "1.0.0";\n'
        '    private static final String HOOK = "kb_client_handler";\n\n'
        "    private static KBClientMod instance;\n"
        "    public static Logger logger;\n\n"
        "    private final KBTracker tracker = new KBTracker();\n"
        "    private KeyBinding openKey;\n"
        "    private Channel hookedChannel;\n"
        "    private boolean pendingOpen;\n"
        "    private Object lastWorld;\n"
        "    private boolean loadingInstalled;",
        '    public static final String VERSION = "1.0.0";\n'
        '    private static final String HOOK = "kb_client_handler";\n'
        "    private static final int RECONNECT_BTN_ID = 9001;\n\n"
        "    private static KBClientMod instance;\n"
        "    public static Logger logger;\n\n"
        "    private final KBTracker tracker = new KBTracker();\n"
        "    private KeyBinding openKey;\n"
        "    private Channel hookedChannel;\n"
        "    private boolean pendingOpen;\n"
        "    private Object lastWorld;\n"
        "    private boolean loadingInstalled;\n"
        "    private ServerData lastServer;",
        "KBClientMod: reconnect fields",
    ),
    (
        "src/main/java/com/oryvex/kbclient/KBClientMod.java",
        "    @SubscribeEvent\n"
        "    public void onInitGui(GuiScreenEvent.InitGuiEvent.Post e) {\n"
        "        if (!(e.gui instanceof GuiIngameMenu)) return;\n"
        "        for (int i = 0; i < e.buttonList.size(); i++) {\n"
        "            GuiButton b = e.buttonList.get(i);\n"
        "            if (b.id == 0) {\n"
        "                UiButton u = new UiButton(0, b.xPosition, b.yPosition, b.width, b.height, b.displayString);\n"
        "                u.icon = UiButton.ICON_GEAR;\n"
        "                e.buttonList.set(i, u);\n"
        "            }\n"
        "        }\n"
        "    }",
        "    @SubscribeEvent\n"
        "    public void onInitGui(GuiScreenEvent.InitGuiEvent.Post e) {\n"
        "        if (e.gui instanceof GuiIngameMenu) {\n"
        "            for (int i = 0; i < e.buttonList.size(); i++) {\n"
        "                GuiButton b = e.buttonList.get(i);\n"
        "                if (b.id == 0) {\n"
        "                    UiButton u = new UiButton(0, b.xPosition, b.yPosition, b.width, b.height, b.displayString);\n"
        "                    u.icon = UiButton.ICON_GEAR;\n"
        "                    e.buttonList.set(i, u);\n"
        "                }\n"
        "            }\n"
        "            return;\n"
        "        }\n\n"
        "        if (e.gui instanceof GuiDisconnected) {\n"
        "            int bw = 200, bh = 20;\n"
        "            UiButton reconnect = new UiButton(RECONNECT_BTN_ID, e.gui.width / 2 - bw / 2, e.gui.height / 4 + 108, bw, bh, \"Reconnect\");\n"
        "            reconnect.style(UiButton.PRIMARY);\n"
        "            reconnect.enabled = lastServer != null;\n"
        "            e.buttonList.add(reconnect);\n"
        "        }\n"
        "    }\n\n"
        "    /** Handles our injected \"Reconnect\" button on the Disconnected screen. */\n"
        "    @SubscribeEvent\n"
        "    public void onAction(GuiScreenEvent.ActionPerformedEvent.Pre e) {\n"
        "        if (!(e.gui instanceof GuiDisconnected) || e.button == null || e.button.id != RECONNECT_BTN_ID) return;\n"
        "        e.setCanceled(true);\n"
        "        if (lastServer != null) {\n"
        "            Minecraft.getMinecraft().displayGuiScreen(new GuiConnecting(e.gui, Minecraft.getMinecraft(), lastServer));\n"
        "        }\n"
        "    }",
        "KBClientMod: reconnect button + handler",
    ),
    (
        "src/main/java/com/oryvex/kbclient/KBClientMod.java",
        "            String name = mc.isSingleplayer() ? \"Singleplayer\"\n"
        "                    : (mc.getCurrentServerData() != null ? mc.getCurrentServerData().serverIP : \"Server\");\n"
        "            tracker.onConnect(name);",
        "            String name = mc.isSingleplayer() ? \"Singleplayer\"\n"
        "                    : (mc.getCurrentServerData() != null ? mc.getCurrentServerData().serverIP : \"Server\");\n"
        "            if (!mc.isSingleplayer() && mc.getCurrentServerData() != null) lastServer = mc.getCurrentServerData();\n"
        "            tracker.onConnect(name);",
        "KBClientMod: remember last server for reconnect",
    ),

    # 4) UiButton - fade only, no slide, no spin
    (
        "src/main/java/com/oryvex/kbclient/ui/UiButton.java",
        "/** Flat rounded button: hover animation, staggered entrance, toggle switch, animated gear icon. */",
        "/** Flat rounded button: fade-in entrance only, toggle switch, static gear icon. */",
        "UiButton: doc comment",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/UiButton.java",
        "    private float hover, knob, spin;",
        "    private float hover, knob;",
        "UiButton: drop spin field",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/UiButton.java",
        "        knob += ((on ? 1f : 0f) - knob) * Math.min(1f, dt * 16f);\n"
        "        spin = (spin + dt * (40f + 380f * hover)) % 360f;\n\n"
        "        float ap = Fade.ease((System.currentTimeMillis() - born - delay) / 320f);\n"
        "        if (ap <= 0.01f) return;\n\n"
        "        int x = xPosition, y = yPosition + (int) ((1f - ap) * 8f), w = width, h = height;",
        "        knob += ((on ? 1f : 0f) - knob) * Math.min(1f, dt * 16f);\n\n"
        "        // fade in only - no slide, no spin\n"
        "        float ap = Fade.ease((System.currentTimeMillis() - born - delay) / 320f);\n"
        "        if (ap <= 0.01f) return;\n\n"
        "        int x = xPosition, y = yPosition, w = width, h = height;",
        "UiButton: fade-only entrance",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/UiButton.java",
        "Draw.gear(startX + 6f, cy, 5.5f, spin, Draw.fade(Draw.lerp(Theme.MUTED, Theme.ACCENT, hover), ap), Draw.fade(fill, ap));",
        "Draw.gear(startX + 6f, cy, 5.5f, 0f, Draw.fade(Draw.lerp(Theme.MUTED, Theme.ACCENT, hover), ap), Draw.fade(fill, ap));",
        "UiButton: static gear icon",
    ),

    # 5) Hud - toast fade only + watermark
    (
        "src/main/java/com/oryvex/kbclient/ui/Hud.java",
        "import java.util.ArrayList;\nimport java.util.List;\nimport net.minecraft.client.Minecraft;",
        "import java.util.ArrayList;\nimport java.util.List;\nimport net.minecraft.client.Minecraft;\nimport net.minecraft.client.gui.ScaledResolution;",
        "Hud: import ScaledResolution",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/Hud.java",
        "    public static void render(Minecraft mc, KBTracker t) {\n        long ns = System.nanoTime();",
        "    public static void render(Minecraft mc, KBTracker t) {\n"
        "        ScaledResolution res = new ScaledResolution(mc);\n"
        "        Draw.blend();\n"
        '        Draw.right("Created by muvixo", res.getScaledWidth() - 4, res.getScaledHeight() - 10, Theme.DIM, 0.7f, false);\n\n'
        "        long ns = System.nanoTime();",
        "Hud: watermark",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/Hud.java",
        "            long age = now - to.born;\n"
        "            float fade = (age > 2800 ? 1f - (age - 2800) / 800f : 1f) * a;\n"
        "            float slide = age < 160 ? (1f - age / 160f) * 10f : 0f;\n"
        "            int tw = Draw.width(to.text, 0.85f) + 12;\n"
        "            Draw.blend();\n"
        "            Draw.roundRect(x - (int) slide, ty, tw, 12, 3, Draw.alpha(0x101826, 0.85f * fade));\n"
        "            int al = (int) (255 * fade);\n"
        "            if (al > 4) Draw.text(to.text, x + 6 - slide, ty + 2, (al << 24) | (to.color & 0xFFFFFF), 0.85f, false);",
        "            long age = now - to.born;\n"
        "            float in = age < 160 ? age / 160f : 1f; // fade in only - no slide\n"
        "            float fade = (age > 2800 ? 1f - (age - 2800) / 800f : 1f) * in * a;\n"
        "            int tw = Draw.width(to.text, 0.85f) + 12;\n"
        "            Draw.blend();\n"
        "            Draw.roundRect(x, ty, tw, 12, 3, Draw.alpha(0x101826, 0.85f * fade));\n"
        "            int al = (int) (255 * fade);\n"
        "            if (al > 4) Draw.text(to.text, x + 6, ty + 2, (al << 24) | (to.color & 0xFFFFFF), 0.85f, false);",
        "Hud: toast fade-only entrance",
    ),

    # 6) watermark - main menu + loading screen
    (
        "src/main/java/com/oryvex/kbclient/ui/GuiModernMenu.java",
        'Draw.text("KB Client 1.0", 6, this.height - 12, Theme.DIM, 0.8f, false);\n'
        '        Draw.right("Forge 1.8.9", this.width - 6, this.height - 12, Theme.DIM, 0.8f, false);',
        'Draw.text("KB Client 1.0", 6, this.height - 12, Theme.DIM, 0.8f, false);\n'
        '        Draw.right("Forge 1.8.9", this.width - 6, this.height - 12, Theme.DIM, 0.8f, false);\n'
        '        Draw.right("Created by muvixo", this.width - 6, this.height - 22, Theme.DIM, 0.7f, false);',
        "GuiModernMenu: watermark",
    ),
    (
        "src/main/java/com/oryvex/kbclient/ui/LoadingArt.java",
        'Draw.text("KB Client 1.0", 6, h - 12, Theme.DIM, 0.75f, false);\n    \n    }',
        'Draw.text("KB Client 1.0", 6, h - 12, Theme.DIM, 0.75f, false);\n'
        '        Draw.right("Created by muvixo", w - 6, h - 12, Theme.DIM, 0.75f, false);\n    \n    }',
        "LoadingArt: watermark",
    ),

    # 7) ProGuard step in the CI workflow
    (
        ".github/workflows/build.yml",
        "      - name: Upload Mod Artifact\n"
        "        uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: KBClient-1.8.9\n"
        "          path: build/libs/*.jar",
        "      - name: Upload Mod Artifact\n"
        "        uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: KBClient-1.8.9\n"
        "          path: build/libs/*.jar\n\n"
        "      - name: Obfuscate with ProGuard\n"
        "        run: |\n"
        "          curl -sL -o proguard.zip https://github.com/Guardsquare/proguard/releases/download/v7.4.2/proguard-7.4.2.zip\n"
        "          unzip -q proguard.zip\n"
        "          mkdir -p build/obf\n"
        "          for jar in build/libs/*.jar; do\n"
        "            name=$(basename \"$jar\" .jar)\n"
        "            proguard-7.4.2/bin/proguard.sh \\\n"
        "              -injars \"$jar\" \\\n"
        "              -outjars \"build/obf/${name}-obf.jar\" \\\n"
        "              @proguard-rules.pro\n"
        "          done\n\n"
        "      - name: Upload Obfuscated Artifact\n"
        "        uses: actions/upload-artifact@v4\n"
        "        with:\n"
        "          name: KBClient-1.8.9-obfuscated\n"
        "          path: build/obf/*.jar",
        "CI: add ProGuard obfuscation step",
    ),
]

# ---------------------------------------------------------------------------
# whole new files: (relative_path, content)
# ---------------------------------------------------------------------------
NEW_FILES = {
    "proguard-rules.pro": """# ProGuard rules for KB Client (Forge 1.8.9 client mod)
# Run against the built mod jar only (Minecraft/Forge/Netty classes are not
# reprocessed - they're just referenced, so warnings about them are expected).

-dontoptimize
-dontpreverify
-dontwarn **
-ignorewarnings

-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

# Forge finds the mod entry point by its @Mod annotation and calls its
# @EventHandler lifecycle methods by reflection - both must survive.
-keep @net.minecraftforge.fml.common.Mod class * {
    @net.minecraftforge.fml.common.Mod$EventHandler <methods>;
}

# Forge's event bus finds listeners by @SubscribeEvent via reflection.
-keepclassmembers class * {
    @net.minecraftforge.fml.common.eventhandler.SubscribeEvent <methods>;
}

# Registered client command - keep its identity/usage strings and dispatch.
-keep class com.oryvex.kbclient.KBCommand { *; }

# Keep enum semantics (values()/valueOf() are used reflectively by libraries).
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}
""",
}


def backup(rel_path, backup_dir):
    src = os.path.join(ROOT, rel_path)
    if not os.path.exists(src):
        return
    dst = os.path.join(backup_dir, rel_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(ROOT, ".fixer_backup", ts)
    manifest = []
    applied, skipped, missing = [], [], []

    # back up every file this run could touch, before changing anything
    touched = sorted({p for p, *_ in PATCHES} | set(NEW_FILES))
    for rel in touched:
        backup(rel, backup_dir)

    for rel, old, new, label in PATCHES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            missing.append((rel, label, "file not found"))
            continue
        content = read(path)
        if new in content:
            skipped.append((rel, label))
            continue
        if old not in content:
            missing.append((rel, label, "anchor text not found - source has drifted, apply by hand"))
            continue
        write(path, content.replace(old, new, 1))
        applied.append((rel, label))
        if not any(m.startswith("M ") and m.endswith(rel) for m in manifest):
            manifest.append("M " + rel)

    for rel, content in NEW_FILES.items():
        path = os.path.join(ROOT, rel)
        exists = os.path.exists(path)
        if exists and read(path).strip() == content.strip():
            skipped.append((rel, "already present"))
            continue
        write(path, content)
        applied.append((rel, "create file"))
        manifest.append(("M " if exists else "C ") + rel)

    if manifest:
        with open(os.path.join(backup_dir, "fixer_manifest.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(manifest) + "\n")

    print("KB Client fixer.py - 1.0.0 pass")
    print("=" * 40)
    for rel, label in applied:
        print("  [applied] %-60s %s" % (rel, label))
    for rel, label in skipped:
        print("  [skip]    %-60s %s (already applied)" % (rel, label))
    for rel, label, why in missing:
        print("  [MISSING] %-60s %s -- %s" % (rel, label, why))

    if applied:
        print("\nBacked up originals to: %s" % os.path.relpath(backup_dir, ROOT))
    else:
        # nothing changed, backup folder is empty/pointless - remove it
        try:
            for r, _, files in os.walk(backup_dir, topdown=False):
                for fn in files:
                    os.remove(os.path.join(r, fn))
                os.rmdir(r)
        except OSError:
            pass

    if missing:
        print("\n%d patch(es) could not be applied automatically - see MISSING above." % len(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()