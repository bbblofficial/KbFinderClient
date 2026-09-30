#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adder.py - Adds Discord Rich Presence support to the KB Client (Forge 1.8.9) project.

Run this from the project root (where build.gradle lives):
    python adder.py

What it does:
  1. Creates src/main/java/com/oryvex/kbclient/DiscordRPC.java
  2. Patches KBClientMod.java  (starts RPC + shutdown hook)
  3. Patches Settings.java     (adds discordRpc preference)
  4. Patches GuiKbOptions.java (adds the toggle button)
  5. Patches build.gradle      (adds the discord-rpc dependency + shading)
  6. Backs up every modified file to .fixer_backup/<timestamp>/

Safe to re-run: already-applied patches are detected and skipped.
"""

import os
import re
import sys
import shutil
import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = os.path.abspath(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src", "main", "java", "com", "oryvex", "kbclient")
UI = os.path.join(SRC, "ui")
BUILD_GRADLE = os.path.join(ROOT, "build.gradle")

STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = os.path.join(ROOT, ".fixer_backup", STAMP)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log(msg):
    print(f"[adder] {msg}")

def warn(msg):
    print(f"[adder] !! {msg}")

def die(msg):
    print(f"[adder] FATAL: {msg}")
    sys.exit(1)

def backup(path):
    """Copy `path` into the timestamped backup folder, preserving structure."""
    if not os.path.isfile(path):
        return
    rel = os.path.relpath(path, ROOT)
    dst = os.path.join(BACKUP, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(path, dst)

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def patch(path, old, new, label, required=True):
    """
    Replace `old` with `new` in `path`.
    Returns True if the file was modified.
    If `old` is not found and `new` is already present, it's a no-op.
    If `old` is not found and `new` is not present either, it errors (required) or warns.
    """
    if not os.path.isfile(path):
        if required:
            die(f"missing file: {path}")
        warn(f"skipping {label}: file not found ({path})")
        return False

    text = read(path)
    if new in text and old not in text:
        log(f"{label}: already applied, skipping")
        return False
    if old not in text:
        if required:
            die(f"{label}: anchor not found in {os.path.basename(path)}")
        warn(f"{label}: anchor not found in {os.path.basename(path)}, skipping")
        return False

    backup(path)
    write(path, text.replace(old, new, 1))
    log(f"{label}: patched {os.path.basename(path)}")
    return True

# ---------------------------------------------------------------------------
# 1. DiscordRPC.java
# ---------------------------------------------------------------------------
DISCORD_RPC_JAVA = r'''package com.oryvex.kbclient;

import club.minnced.discord.rpc.DiscordEventHandlers;
import club.minnced.discord.rpc.DiscordRPC;
import club.minnced.discord.rpc.DiscordRichPresence;
import net.minecraft.client.Minecraft;

/**
 * Discord Rich Presence for KB Client.
 *
 * Create a Discord Application at https://discord.com/developers/applications
 * and put its Application ID into APP_ID below. Upload image assets named
 * "oryvex" and "minecraft" in the Rich Presence -> Art Assets tab.
 */
public final class DiscordRPC {
    /** TODO: replace with your own Discord Application ID. */
    private static final String APP_ID = "1234567890123456789";

    private static club.minnced.discord.rpc.DiscordRPC rpc;
    private static DiscordRichPresence presence;
    private static Thread worker;
    private static volatile boolean running;
    private static long startTime;
    private static String lastDetails = "";
    private static String lastState = "";

    private DiscordRPC() {}

    public static synchronized void start() {
        if (running) return;
        if (APP_ID.startsWith("1234")) {
            KBClientMod.logger.warn("[KBClient] Discord RPC disabled: set your APP_ID in DiscordRPC.java");
            return;
        }
        try {
            rpc = club.minnced.discord.rpc.DiscordRPC.INSTANCE;

            DiscordEventHandlers handlers = new DiscordEventHandlers();
            handlers.ready = user -> KBClientMod.logger.info("[KBClient] Discord RPC ready for " + user.username);
            handlers.disconnected = (code, msg) -> KBClientMod.logger.warn("[KBClient] Discord RPC disconnected: " + code + " " + msg);
            handlers.errored = (code, msg) -> KBClientMod.logger.warn("[KBClient] Discord RPC error: " + code + " " + msg);

            rpc.Discord_Initialize(APP_ID, handlers, true, null);

            startTime = System.currentTimeMillis() / 1000L;
            presence = new DiscordRichPresence();
            presence.startTimestamp = startTime;
            presence.largeImageKey = "oryvex";
            presence.largeImageText = "KB Client 3.0";
            presence.smallImageKey = "minecraft";
            presence.smallImageText = "Minecraft 1.8.9";
            presence.details = "In the menus";
            presence.state = "Idle";
            rpc.Discord_UpdatePresence(presence);

            running = true;
            worker = new Thread(DiscordRPC::loop, "KBClient-DiscordRPC");
            worker.setDaemon(true);
            worker.start();

            KBClientMod.logger.info("[KBClient] Discord RPC started");
        } catch (Throwable t) {
            KBClientMod.logger.error("[KBClient] Discord RPC init failed: " + t);
        }
    }

    private static void loop() {
        while (running) {
            try {
                rpc.Discord_RunCallbacks();
                updatePresence();
                Thread.sleep(2000L);
            } catch (InterruptedException e) {
                break;
            } catch (Throwable t) {
                KBClientMod.logger.warn("[KBClient] Discord RPC loop error: " + t);
            }
        }
    }

    private static void updatePresence() {
        Minecraft mc = Minecraft.getMinecraft();
        String details;
        String state;

        if (mc.theWorld == null) {
            details = "In the menus";
            state = "KB Client 3.0";
        } else if (mc.isSingleplayer()) {
            details = "Singleplayer";
            String worldName = "world";
            try {
                if (mc.getIntegratedServer() != null) worldName = mc.getIntegratedServer().getWorldName();
            } catch (Throwable ignored) { }
            state = "World: " + worldName;
        } else {
            String ip = (mc.getCurrentServerData() != null)
                    ? mc.getCurrentServerData().serverIP
                    : "Unknown server";
            details = "Playing on " + ip;
            int players = (mc.theWorld != null) ? mc.theWorld.playerEntities.size() : 0;
            state = players + " players online";
        }

        if (details.equals(lastDetails) && state.equals(lastState)) return;
        lastDetails = details;
        lastState = state;

        presence.details = details;
        presence.state = state;
        presence.startTimestamp = startTime;
        rpc.Discord_UpdatePresence(presence);
    }

    public static synchronized void stop() {
        if (!running) return;
        running = false;
        try {
            if (worker != null) worker.interrupt();
            if (rpc != null) {
                rpc.Discord_ClearPresence();
                rpc.Discord_Shutdown();
            }
        } catch (Throwable ignored) { }
        rpc = null;
        presence = null;
        KBClientMod.logger.info("[KBClient] Discord RPC stopped");
    }

    public static boolean isRunning() {
        return running;
    }
}
'''

def create_discord_rpc():
    path = os.path.join(SRC, "DiscordRPC.java")
    if os.path.isfile(path):
        log("DiscordRPC.java: already exists, skipping")
        return
    os.makedirs(SRC, exist_ok=True)
    write(path, DISCORD_RPC_JAVA)
    log("DiscordRPC.java: created")

# ---------------------------------------------------------------------------
# 2. KBClientMod.java
# ---------------------------------------------------------------------------
def patch_kbclientmod():
    path = os.path.join(SRC, "KBClientMod.java")

    # (a) start RPC in init()
    patch(
        path,
        "        ClientRegistry.registerKeyBinding(openKey);\n"
        "        installLoading();\n"
        "    }",
        "        ClientRegistry.registerKeyBinding(openKey);\n"
        "        installLoading();\n"
        "        if (Settings.discordRpc) DiscordRPC.start();\n"
        "        Runtime.getRuntime().addShutdownHook(new Thread(DiscordRPC::stop, \"KBClient-RPC-Shutdown\"));\n"
        "    }",
        "KBClientMod.init() -> DiscordRPC.start()"
    )

# ---------------------------------------------------------------------------
# 3. Settings.java
# ---------------------------------------------------------------------------
def patch_settings():
    path = os.path.join(UI, "Settings.java")

    # (a) field
    patch(
        path,
        "    public static boolean customLoading = true;\n"
        "    public static int fade = 2;",
        "    public static boolean customLoading = true;\n"
        "    public static boolean discordRpc = true;\n"
        "    public static int fade = 2;",
        "Settings field"
    )

    # (b) load()
    patch(
        path,
        '            customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));\n'
        '            fade = Math.max(0, Math.min(3, Integer.parseInt(p.getProperty("fade", "2"))));',
        '            customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));\n'
        '            discordRpc = Boolean.parseBoolean(p.getProperty("discordRpc", "true"));\n'
        '            fade = Math.max(0, Math.min(3, Integer.parseInt(p.getProperty("fade", "2"))));',
        "Settings.load()"
    )

    # (c) save()
    patch(
        path,
        '            p.setProperty("customLoading", String.valueOf(customLoading));\n'
        '            p.setProperty("fade", String.valueOf(fade));',
        '            p.setProperty("customLoading", String.valueOf(customLoading));\n'
        '            p.setProperty("discordRpc", String.valueOf(discordRpc));\n'
        '            p.setProperty("fade", String.valueOf(fade));',
        "Settings.save()"
    )

# ---------------------------------------------------------------------------
# 4. GuiKbOptions.java
# ---------------------------------------------------------------------------
def patch_gui_options():
    path = os.path.join(UI, "GuiKbOptions.java")

    # (a) field declaration
    patch(
        path,
        "    private UiButton bHud, bPart, bToast, bLoad, bFade;",
        "    private UiButton bHud, bPart, bToast, bLoad, bFade, bRpc;",
        "GuiKbOptions field"
    )

    # (b) card height: add one more row (+bh+gap)
    patch(
        path,
        "        cardH = 7 * (bh + gap) + 62;",
        "        cardH = 8 * (bh + gap) + 62;",
        "GuiKbOptions card height"
    )

    # (c) add the button + shift Done/MC Options down by one row
    patch(
        path,
        '        bFade = new UiButton(5, cx - bw / 2, y + 4 * (bh + gap), bw, bh, "").delay(260);\n'
        '        this.buttonList.add(bHud);\n'
        '        this.buttonList.add(bPart);\n'
        '        this.buttonList.add(bToast);\n'
        '        this.buttonList.add(bLoad);\n'
        '        this.buttonList.add(bFade);\n'
        '        this.buttonList.add(new UiButton(6, cx - bw / 2, y + 5 * (bh + gap) + 8, bw, bh, "Minecraft Options...").icon(UiButton.ICON_GEAR).delay(310));\n'
        '        this.buttonList.add(new UiButton(7, cx - bw / 2, y + 6 * (bh + gap) + 8, bw, bh, "Done").style(UiButton.PRIMARY).delay(360));',
        '        bFade = new UiButton(5, cx - bw / 2, y + 4 * (bh + gap), bw, bh, "").delay(260);\n'
        '        bRpc = new UiButton(8, cx - bw / 2, y + 5 * (bh + gap), bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(290);\n'
        '        this.buttonList.add(bHud);\n'
        '        this.buttonList.add(bPart);\n'
        '        this.buttonList.add(bToast);\n'
        '        this.buttonList.add(bLoad);\n'
        '        this.buttonList.add(bFade);\n'
        '        this.buttonList.add(bRpc);\n'
        '        this.buttonList.add(new UiButton(6, cx - bw / 2, y + 6 * (bh + gap) + 8, bw, bh, "Minecraft Options...").icon(UiButton.ICON_GEAR).delay(310));\n'
        '        this.buttonList.add(new UiButton(7, cx - bw / 2, y + 7 * (bh + gap) + 8, bw, bh, "Done").style(UiButton.PRIMARY).delay(360));',
        "GuiKbOptions buttons"
    )

    # (d) sync()
    patch(
        path,
        "        bLoad.on = Settings.customLoading;\n"
        "        bFade.displayString = \"Screen fades: \" + Settings.FADE_NAMES[Settings.fade];",
        "        bLoad.on = Settings.customLoading;\n"
        "        if (bRpc != null) bRpc.on = Settings.discordRpc;\n"
        "        bFade.displayString = \"Screen fades: \" + Settings.FADE_NAMES[Settings.fade];",
        "GuiKbOptions.sync()"
    )

    # (e) actionPerformed case 8
    patch(
        path,
        '              case 5: Settings.fade = (Settings.fade + 1) % 4; break;',
        '              case 5: Settings.fade = (Settings.fade + 1) % 4; break;\n'
        '              case 8:\n'
        '                  Settings.discordRpc = !Settings.discordRpc;\n'
        '                  if (Settings.discordRpc) com.oryvex.kbclient.DiscordRPC.start();\n'
        '                  else com.oryvex.kbclient.DiscordRPC.stop();\n'
        '                  break;',
        "GuiKbOptions.actionPerformed case 8"
    )

# ---------------------------------------------------------------------------
# 5. build.gradle
# ---------------------------------------------------------------------------
GRADLE_BLOCK = """
// ---- KB Client: Discord Rich Presence ---------------------------------------
repositories {
    maven { url 'https://jitpack.io' }
}

configurations {
    shade
    compile.extendsFrom shade
}

dependencies {
    shade 'com.github.MinnDevelopment:java-discord-rpc:v2.0.2'
}

jar {
    configurations.shade.each { dep ->
        from(project.zipTree(dep)) {
            exclude 'META-INF', 'META-INF/**'
        }
    }
}
// ----------------------------------------------------------------------------
"""

def patch_build_gradle():
    if not os.path.isfile(BUILD_GRADLE):
        warn("build.gradle not found; skipping gradle patch")
        return

    text = read(BUILD_GRADLE)
    if "java-discord-rpc" in text:
        log("build.gradle: already patched, skipping")
        return

    backup(BUILD_GRADLE)
    write(BUILD_GRADLE, text.rstrip() + "\n" + GRADLE_BLOCK)
    log("build.gradle: appended Discord RPC block")

# ---------------------------------------------------------------------------
# 6. Build sanity check
# ---------------------------------------------------------------------------
def sanity_check():
    missing = []
    for p in (os.path.join(SRC, "KBClientMod.java"),
              os.path.join(SRC, "DiscordRPC.java"),
              os.path.join(UI, "Settings.java"),
              os.path.join(UI, "GuiKbOptions.java")):
        if not os.path.isfile(p):
            missing.append(os.path.relpath(p, ROOT))

    if missing:
        warn("these files are missing and were NOT patched:")
        for m in missing:
            warn("  - " + m)
        return False
    return True

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 64)
    print(" KB Client - Discord Rich Presence adder")
    print("=" * 64)
    print(f" project root : {ROOT}")
    print(f" backup dir   : {os.path.relpath(BACKUP, ROOT)}")
    print()

    if not os.path.isdir(SRC):
        die(f"source dir not found: {SRC}\n"
            f"Run this script from the project root (next to build.gradle).")

    os.makedirs(BACKUP, exist_ok=True)

    create_discord_rpc()
    patch_kbclientmod()
    patch_settings()
    patch_gui_options()
    patch_build_gradle()

    print()
    if sanity_check():
        log("done. all patches applied.")
    else:
        warn("done, but some files were missing - check the warnings above.")

    print()
    print("Next steps:")
    print("  1. Open DiscordRPC.java and set APP_ID to your Discord Application ID.")
    print("     https://discord.com/developers/applications")
    print("  2. Upload asset keys 'oryvex' (large) and 'minecraft' (small)")
    print("     in Rich Presence -> Art Assets.")
    print("  3. Build:  ./gradlew build")
    print("  4. Run:    ./gradlew runClient")
    print()
    print(f"Backups (if any) are in: {os.path.relpath(BACKUP, ROOT)}")


if __name__ == "__main__":
    main()