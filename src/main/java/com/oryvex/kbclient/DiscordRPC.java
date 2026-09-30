package com.oryvex.kbclient;

import net.minecraft.client.Minecraft;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.lang.management.ManagementFactory;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/**
 * Discord Rich Presence - diagnostic build.
 * Logs every step so you can see exactly where it fails.
 */
public final class DiscordRPC {

    /** TODO: replace with your own Discord Application ID. */
    private static final String APP_ID = "1554952903758716989";

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
            KBClientMod.logger.warn("[KB-RPC] disabled: APP_ID is still the placeholder");
            return;
        }
        KBClientMod.logger.info("[KB-RPC] starting with APP_ID=" + APP_ID);

        if (!connect()) {
            KBClientMod.logger.warn("[KB-RPC] no Discord IPC socket found. Is the Discord desktop app running?");
            return;
        }
        try {
            sendHandshake();
            String reply = readFrame(1000);
            KBClientMod.logger.info("[KB-RPC] handshake reply: " + reply);
            if (reply == null || !reply.contains("\"READY\"")) {
                KBClientMod.logger.warn("[KB-RPC] handshake failed, aborting");
                close();
                return;
            }
            startTime = System.currentTimeMillis() / 1000L;
            updatePresence(true);
        } catch (IOException e) {
            KBClientMod.logger.warn("[KB-RPC] handshake exception: " + e);
            close();
            return;
        }

        running = true;
        worker = new Thread(DiscordRPC::loop, "KBClient-DiscordRPC");
        worker.setDaemon(true);
        worker.start();
        KBClientMod.logger.info("[KB-RPC] running");
    }

    public static synchronized void stop() {
        if (!running) return;
        running = false;
        try { sendFrame(OP_CLOSE, "{}"); } catch (IOException ignored) { }
        if (worker != null) worker.interrupt();
        close();
        KBClientMod.logger.info("[KB-RPC] stopped");
    }

    public static boolean isRunning() { return running; }

    // ------------------------------------------------------------------
    // socket
    // ------------------------------------------------------------------
    private static boolean connect() {
        String os = System.getProperty("os.name", "").toLowerCase();
        boolean win = os.contains("win");
        KBClientMod.logger.info("[KB-RPC] OS=" + os + " (windows=" + win + ")");

        if (win) {
            String[] prefixes = { "\\\\?\\pipe\\discord-ipc-", "\\\\.\\pipe\\discord-ipc-" };
            for (String pfx : prefixes) {
                for (int i = 0; i < 10; i++) {
                    String path = pfx + i;
                    try {
                        pipe = new RandomAccessFile(path, "rw");
                        KBClientMod.logger.info("[KB-RPC] connected: " + path);
                        return true;
                    } catch (IOException e) {
                        // keep quiet, try next
                    }
                }
            }
        } else {
            // Unix domain socket - Java 8 RandomAccessFile cannot open these
            // on Linux/macOS. This branch is here only so the log makes sense.
            for (int i = 0; i < 10; i++) {
                String path = "/tmp/discord-ipc-" + i;
                try {
                    pipe = new RandomAccessFile(path, "rw");
                    KBClientMod.logger.info("[KB-RPC] connected: " + path);
                    return true;
                } catch (IOException e) {
                    // try next
                }
            }
            KBClientMod.logger.warn("[KB-RPC] unix socket open failed. Java 8 on Linux/macOS");
            KBClientMod.logger.warn("[KB-RPC] cannot connect to Discord IPC. Windows is required");
            KBClientMod.logger.warn("[KB-RPC] for the dependency-free version. Add JNA later if needed.");
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
        KBClientMod.logger.info("[KB-RPC] -> handshake " + json);
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

    /** Read one frame with a soft timeout. Returns null on timeout. */
    private static String readFrame(int timeoutMs) {
        try {
            long deadline = System.currentTimeMillis() + timeoutMs;
            // RandomAccessFile doesn't support timeouts; do a quick availability check.
            while (pipe.length() < 8) {
                if (System.currentTimeMillis() > deadline) return null;
                Thread.sleep(20);
            }
            byte[] header = new byte[8];
            pipe.readFully(header);
            ByteBuffer hb = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);
            int op = hb.getInt();
            int len = hb.getInt();
            if (len < 0 || len > (1 << 20)) throw new IOException("bad frame len " + len);
            byte[] body = new byte[len];
            pipe.readFully(body);
            String json = new String(body, StandardCharsets.UTF_8);
            KBClientMod.logger.info("[KB-RPC] <- op=" + op + " " + json);
            return json;
        } catch (Throwable t) {
            KBClientMod.logger.warn("[KB-RPC] readFrame error: " + t);
            return null;
        }
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
                KBClientMod.logger.warn("[KB-RPC] loop error: " + t);
                break;
            }
        }
    }

    private static void updatePresence(boolean force) {
        Minecraft mc = Minecraft.getMinecraft();
        String details, state;

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
            state = mc.theWorld.playerEntities.size() + " players online";
        }

        if (!force && details.equals(lastDetails) && state.equals(lastState)) return;
        lastDetails = details;
        lastState = state;

        long pid = currentPid();
        String json = "{"
                + "\"cmd\":\"SET_ACTIVITY\","
                + "\"args\":{"
                +   "\"pid\":" + pid + ","
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
            KBClientMod.logger.info("[KB-RPC] -> activity (pid=" + pid + ")");
            sendFrame(OP_FRAME, json);
            readFrame(800);
        } catch (IOException e) {
            KBClientMod.logger.warn("[KB-RPC] send failed: " + e);
            running = false;
        }
    }

    private static long currentPid() {
        try {
            String name = ManagementFactory.getRuntimeMXBean().getName();
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