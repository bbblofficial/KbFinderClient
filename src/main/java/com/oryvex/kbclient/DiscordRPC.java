package com.oryvex.kbclient;

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
    private static final String APP_ID = "12345671554952903758716989890123456789";

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
