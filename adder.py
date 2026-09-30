#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adder.py - Adds Discord Rich Presence support to the KB Client (Forge 1.8.9) project.

This version has ZERO external dependencies - it talks the Discord IPC protocol
directly over the local socket. No shading, no ForgeGradle 2.1 headaches.

Run from the project root (where build.gradle lives):
    python adder.py

What it does:
  1. Creates src/main/java/com/oryvex/kbclient/DiscordRPC.java (dependency-free)
  2. Patches KBClientMod.java   (starts RPC + shutdown hook)
  3. Patches Settings.java      (adds the discordRpc preference)
  4. Patches GuiKbOptions.java  (adds the toggle button)
  5. CLEANS build.gradle        (removes any previous 'shade'/'java-discord-rpc' block)
  6. Backs up every modified file to .fixer_backup/<timestamp>/

Safe to re-run: already-applied patches are detected and skipped.
"""

import os
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
    print("[adder] " + msg)

def warn(msg):
    print("[adder] !! " + msg)

def die(msg):
    print("[adder] FATAL: " + msg)
    sys.exit(1)

def backup(path):
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
    if not os.path.isfile(path):
        if required:
            die("missing file: " + path)
        warn("skipping " + label + ": file not found (" + path + ")")
        return False

    text = read(path)
    if new in text and old not in text:
        log(label + ": already applied, skipping")
        return False
    if old not in text:
        if required:
            die(label + ": anchor not found in " + os.path.basename(path))
        warn(label + ": anchor not found in " + os.path.basename(path) + ", skipping")
        return False

    backup(path)
    write(path, text.replace(old, new, 1))
    log(label + ": patched " + os.path.basename(path))
    return True

# ---------------------------------------------------------------------------
# 1. DiscordRPC.java  (pure-Java IPC, no external dependency)
# ---------------------------------------------------------------------------
DISCORD_RPC_JAVA = r'''package com.oryvex.kbclient;

import net.minecraft.client.Minecraft;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/**
 * Minimal Discord Rich Presence client.
 *
 * Talks the Discord IPC protocol directly over the local socket:
 *   - Linux/macOS: /tmp/discord-ipc-{0..9}   (unix domain socket)
 *   - Windows:     \\?\pipe\discord-ipc-{0..9}
 *
 * No external dependency, so no shading / classloader headaches with
 * ForgeGradle 2.1. If Discord is not running the call is a silent no-op.
 *
 * Setup:
 *   1. Create an application at https://discord.com/developers/applications
 *   2. Copy its Application ID into APP_ID below.
 *   3. In "Rich Presence -> Art Assets" upload images named:
 *        - "oryvex"    (large image)
 *        - "minecraft" (small image)
 */
public final class DiscordRPC {

    /** TODO: replace with your own Discord Application ID. */
    private static final String APP_ID = "1234567890123456789";

    private static final int OP_HANDSHAKE = 0;
    private static final int OP_FRAME     = 1;
    private static final int OP_CLOSE     = 2;

    private static RandomAccessFile pipe;
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
        if (!connect()) {
            KBClientMod.logger.info("[KBClient] Discord is not running - RPC stays off");
            return;
        }
        try {
            sendHandshake();
            startTime = System.currentTimeMillis() / 1000L;
            updatePresence(true);
        } catch (IOException e) {
            KBClientMod.logger.warn("[KBClient] Discord handshake failed: " + e);
            close();
            return;
        }

        running = true;
        worker = new Thread(DiscordRPC::loop, "KBClient-DiscordRPC");
        worker.setDaemon(true);
        worker.start();
        KBClientMod.logger.info("[KBClient] Discord RPC started");
    }

    public static synchronized void stop() {
        if (!running) return;
        running = false;
        try { sendFrame(OP_CLOSE, "{}"); } catch (IOException ignored) { }
        if (worker != null) worker.interrupt();
        close();
        KBClientMod.logger.info("[KBClient] Discord RPC stopped");
    }

    public static boolean isRunning() { return running; }

    // ------------------------------------------------------------------
    // socket
    // ------------------------------------------------------------------
    private static boolean connect() {
        String os = System.getProperty("os.name", "").toLowerCase();
        boolean win = os.contains("win");
        for (int i = 0; i < 10; i++) {
            String path = win
                    ? "\\\\?\\pipe\\discord-ipc-" + i
                    : "/tmp/discord-ipc-" + i;
            try {
                pipe = new RandomAccessFile(path, "rw");
                KBClientMod.logger.info("[KBClient] connected to " + path);
                return true;
            } catch (IOException ignored) {
                // try next index
            }
        }
        return false;
    }

    private static void close() {
        if (pipe != null) {
            try { pipe.close(); } catch (IOException ignored) { }
            pipe = null;
        }
    }

    private static void sendHandshake() throws IOException {
        String json = "{\"v\":1,\"client_id\":\"" + APP_ID + "\"}";
        sendFrame(OP_HANDSHAKE, json);
    }

    private static synchronized void sendFrame(int op, String json) throws IOException {
        if (pipe == null) throw new IOException("not connected");
        byte[] payload = json.getBytes(StandardCharsets.UTF_8);
        ByteBuffer buf = ByteBuffer.allocate(8 + payload.length).order(ByteOrder.LITTLE_ENDIAN);
        buf.putInt(op);
        buf.putInt(payload.length);
        buf.put(payload);
        pipe.write(buf.array());
    }

    // ------------------------------------------------------------------
    // presence loop
    // ------------------------------------------------------------------
    private static void loop() {
        while (running) {
            try {
                updatePresence(false);
                Thread.sleep(2000L);
            } catch (InterruptedException e) {
                break;
            } catch (Throwable t) {
                KBClientMod.logger.warn("[KBClient] Discord RPC loop error: " + t);
                break;
            }
        }
    }

    private static void updatePresence(boolean force) {
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
            int players = mc.theWorld.playerEntities.size();
            state = players + " players online";
        }

        if (!force && details.equals(lastDetails) && state.equals(lastState)) return;
        lastDetails = details;
        lastState = state;

        String json = "{"
                + "\"cmd\":\"SET_ACTIVITY\","
                + "\"args\":{"
                +   "\"pid\":" + currentPid() + ","
                +   "\"activity\":{"
                +     "\"details\":" + quote(details) + ","
                +     "\"state\":" + quote(state) + ","
                +     "\"timestamps\":{\"start\":" + startTime + "},"
                +     "\"assets\":{"
                +       "\"large_image\":\"oryvex\","
                +       "\"large_text\":\"KB Client 3.0\","
                +       "\"small_image\":\"minecraft\","
                +       "\"small_text\":\"Minecraft 1.8.9\""
                +     "}"
                +   "}"
                + "},"
                + "\"nonce\":\"" + System.nanoTime() + "\""
                + "}";

        try {
            sendFrame(OP_FRAME, json);
        } catch (IOException e) {
            KBClientMod.logger.warn("[KBClient] Discord send failed, stopping: " + e);
            running = false;
        }
    }

    /** Best-effort PID lookup (Java 8 safe). Falls back to 0 which Discord accepts. */
    private static long currentPid() {
        try {
            String name = java.lang.management.ManagementFactory.getRuntimeMXBean().getName();
            int at = name.indexOf('@');
            if (at > 0) return Long.parseLong(name.substring(0, at));
        } catch (Throwable ignored) { }
        return 0L;
    }

    private static String quote(String s) {
        StringBuilder sb = new StringBuilder(s.length() + 2);
        sb.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"' || c == '\\') sb.append('\\').append(c);
            else if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
            else sb.append(c);
        }
        sb.append('"');
        return sb.toString();
    }
}
'''

def create_discord_rpc():
    path = os.path.join(SRC, "DiscordRPC.java")
    if os.path.isfile(path):
        backup(path)
        log("DiscordRPC.java: overwriting existing file")
    else:
        os.makedirs(SRC, exist_ok=True)
        log("DiscordRPC.java: creating")
    write(path, DISCORD_RPC_JAVA)

# ---------------------------------------------------------------------------
# 2. KBClientMod.java
# ---------------------------------------------------------------------------
def patch_kbclientmod():
    path = os.path.join(SRC, "KBClientMod.java")

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

    patch(
        path,
        "    public static boolean customLoading = true;\n"
        "    public static int fade = 2;",
        "    public static boolean customLoading = true;\n"
        "    public static boolean discordRpc = true;\n"
        "    public static int fade = 2;",
        "Settings field"
    )

    patch(
        path,
        '            customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));\n'
        '            fade = Math.max(0, Math.min(3, Integer.parseInt(p.getProperty("fade", "2"))));',
        '            customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));\n'
        '            discordRpc = Boolean.parseBoolean(p.getProperty("discordRpc", "true"));\n'
        '            fade = Math.max(0, Math.min(3, Integer.parseInt(p.getProperty("fade", "2"))));',
        "Settings.load()"
    )

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

    # (a) field
    patch(
        path,
        "    private UiButton bHud, bPart, bToast, bLoad, bFade;",
        "    private UiButton bHud, bPart, bToast, bLoad, bFade, bRpc;",
        "GuiKbOptions field"
    )

    # (b) card height
    patch(
        path,
        "        cardH = 7 * (bh + gap) + 62;",
        "        cardH = 8 * (bh + gap) + 62;",
        "GuiKbOptions card height"
    )

    # (c) buttons layout
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
# 5. build.gradle cleanup
#    Removes any previous 'shade' / 'java-discord-rpc' block that an older
#    version of adder.py might have added. Adds nothing new.
# ---------------------------------------------------------------------------
def clean_build_gradle():
    if not os.path.isfile(BUILD_GRADLE):
        warn("build.gradle not found; skipping cleanup")
        return

    text = read(BUILD_GRADLE)
    original = text

    # Remove the block that the previous adder.py appended:
    # it starts with the marker comment and runs to the closing '---' line.
    marker_start = "// ---- KB Client: Discord Rich Presence"
    marker_end = "// ----------------------------------------------------------------------------"

    if marker_start in text:
        i = text.find(marker_start)
        # find the end marker AFTER i
        j = text.find(marker_end, i)
        if j != -1:
            j += len(marker_end)
            text = text[:i].rstrip() + "\n" + text[j:].lstrip()
            log("build.gradle: removed old Discord RPC block")

    # Also strip any leftover individual lines just in case.
    leftover = [
        "implementation 'club.minnced:java-discord-rpc",
        "implementation 'com.github.MinnDevelopment:java-discord-rpc",
        "shade 'club.minnced:java-discord-rpc",
        "shade 'com.github.MinnDevelopment:java-discord-rpc",
        "compile 'club.minnced:java-discord-rpc",
        "compile 'com.github.MinnDevelopment:java-discord-rpc",
    ]
    lines = text.split("\n")
    kept = [ln for ln in lines if not any(l in ln for l in leftover)]
    if len(kept) != len(lines):
        text = "\n".join(kept)
        log("build.gradle: removed leftover discord-rpc dependency lines")

    if text != original:
        backup(BUILD_GRADLE)
        write(BUILD_GRADLE, text)
    else:
        log("build.gradle: clean, nothing to remove")

# ---------------------------------------------------------------------------
# 6. Sanity check
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
    print(" KB Client - Discord Rich Presence adder (v2, dependency-free)")
    print("=" * 64)
    print(" project root : " + ROOT)
    print(" backup dir   : " + os.path.relpath(BACKUP, ROOT))
    print()

    if not os.path.isdir(SRC):
        die("source dir not found: " + SRC + "\n"
            "Run this script from the project root (next to build.gradle).")

    os.makedirs(BACKUP, exist_ok=True)

    create_discord_rpc()
    patch_kbclientmod()
    patch_settings()
    patch_gui_options()
    clean_build_gradle()

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
    print(" Backups are in: " + os.path.relpath(BACKUP, ROOT))


if __name__ == "__main__":
    main()