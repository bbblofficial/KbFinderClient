package com.oryvex.kbclient;

import com.oryvex.kbclient.ui.GuiAnalyzer;
import com.oryvex.kbclient.ui.Settings;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.lang.management.ManagementFactory;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ServerData;

/**
 * Discord Rich Presence ("Playing KB Client").  Added by adder.py.
 *
 * No external library: it speaks Discord's local IPC protocol directly over the
 * named pipe \\?\pipe\discord-ipc-N (Windows).  The Discord desktop app must be
 * running.  Art assets "oryvex" (large) and "minecraft" (small) must be uploaded in
 * Developer Portal -> your application -> Rich Presence -> Art Assets.
 */
public final class DiscordRPC {
    public static final String APP_ID = "1554952903758716989";

    private static final String LARGE_KEY = "oryvex";
    private static final String SMALL_KEY = "minecraft";
    /** false = never show the server address in your status */
    private static final boolean SHOW_SERVER_IP = true;

    private static final long MIN_GAP_MS = 5000L;   // Discord allows ~5 updates / 20 s
    private static final long RETRY_MS = 10000L;    // retry when Discord is not running
    private static final boolean WINDOWS = System.getProperty("os.name", "").toLowerCase().contains("win");
    private static final long PID = pid();

    private static volatile boolean active;
    private static volatile int generation;
    private static volatile Activity pending;
    private static Thread worker;
    private static int ticks;
    private static String curKey = "menu";
    private static long curStart;

    private DiscordRPC() {}

    // ---- public api ------------------------------------------------------------
    /** Starts the presence (if enabled in Options). Safe to call repeatedly. */
    public static synchronized void start() {
        if (!Settings.discordRpc || active) return;
        if (!WINDOWS) {
            log("Discord RPC: only supported on Windows, disabled");
            return;
        }
        try {
            if (worker != null && worker.isAlive()) worker.join(500L);
        } catch (InterruptedException ignored) { }

        active = true;
        final int gen = ++generation;
        curKey = "menu";
        curStart = System.currentTimeMillis() / 1000L;
        pending = new Activity("In the menus", "KB Client " + KBClientMod.VERSION, curStart);

        worker = new Thread(() -> loop(gen), "KBClient-DiscordRPC");
        worker.setDaemon(true);
        worker.start();
    }

    /** Clears the presence and stops. */
    public static synchronized void stop() {
        if (!active) return;
        active = false;
        generation++;
        if (worker != null) worker.interrupt();
    }

    /** Call after the Options toggle changed. */
    public static void apply() {
        if (Settings.discordRpc) start(); else stop();
    }

    /** Called every client tick (main thread): samples the game state once per second. */
    public static void tick() {
        if (!active) return;
        if (++ticks < 20) return;
        ticks = 0;
        try {
            Minecraft mc = Minecraft.getMinecraft();
            boolean analyzing = mc.currentScreen instanceof GuiAnalyzer;
            String key, details, state;

            if (mc.theWorld == null) {
                key = "menu";
                details = "In the menus";
                state = "KB Client " + KBClientMod.VERSION;
            } else if (mc.isSingleplayer()) {
                key = "sp";
                details = analyzing ? "Analyzing knockback" : "Playing Singleplayer";
                String world = "world";
                try {
                    if (mc.getIntegratedServer() != null) world = mc.getIntegratedServer().getWorldName();
                } catch (Throwable ignored) { }
                state = "World: " + world;
            } else {
                ServerData sd = mc.getCurrentServerData();
                String ip = (sd != null) ? sd.serverIP : null;
                key = "mp:" + ip;
                details = analyzing ? "Analyzing knockback" : "Playing Multiplayer";
                state = (SHOW_SERVER_IP && ip != null && ip.length() > 0) ? ip : "On a server";
            }

            if (!key.equals(curKey)) {          // joined / left a world or server -> restart timer
                curKey = key;
                curStart = System.currentTimeMillis() / 1000L;
            }
            pending = new Activity(details, state, curStart);
        } catch (Throwable ignored) { }
    }

    // ---- worker ----------------------------------------------------------------
    private static void loop(int gen) {
        Pipe pipe = null;
        String sent = null;
        long lastSend = 0L;
        boolean warned = false;
        try {
            while (generation == gen) {
                try {
                    if (pipe == null) {
                        pipe = Pipe.open(APP_ID);
                        sent = null;
                        warned = false;
                        log("Discord RPC connected");
                    }
                    Activity a = pending;
                    long now = System.currentTimeMillis();
                    if (a != null && !a.sig().equals(sent) && now - lastSend >= MIN_GAP_MS) {
                        pipe.send(a.json());
                        sent = a.sig();
                        lastSend = now;
                    }
                    Thread.sleep(1000L);
                } catch (IOException e) {
                    if (pipe != null) { pipe.close(); pipe = null; }
                    if (!warned) {
                        log("Discord RPC: Discord not reachable (" + e + "), retrying every 10s");
                        warned = true;
                    }
                    Thread.sleep(RETRY_MS);
                }
            }
        } catch (InterruptedException ignored) {
        } catch (Throwable t) {
            log("Discord RPC stopped: " + t);
        } finally {
            if (pipe != null) {
                try { pipe.send(Activity.clearJson()); } catch (Throwable ignored) { }
                pipe.close();
            }
        }
    }

    // ---- data ------------------------------------------------------------------
    private static final class Activity {
        final String details, state;
        final long start;

        Activity(String details, String state, long start) {
            this.details = details;
            this.state = state;
            this.start = start;
        }

        String sig() { return details + "\n" + state + "\n" + start; }

        String json() {
            return "{\"cmd\":\"SET_ACTIVITY\",\"args\":{\"pid\":" + PID + ",\"activity\":{"
                    + "\"details\":\"" + esc(clip(details)) + "\","
                    + "\"state\":\"" + esc(clip(state)) + "\","
                    + "\"timestamps\":{\"start\":" + start + "},"
                    + "\"assets\":{\"large_image\":\"" + LARGE_KEY + "\",\"large_text\":\""
                    + esc("KB Client " + KBClientMod.VERSION) + "\","
                    + "\"small_image\":\"" + SMALL_KEY + "\",\"small_text\":\"Minecraft 1.8.9\"}"
                    + "}},\"nonce\":\"" + UUID.randomUUID() + "\"}";
        }

        static String clearJson() {
            return "{\"cmd\":\"SET_ACTIVITY\",\"args\":{\"pid\":" + PID + "},\"nonce\":\"" + UUID.randomUUID() + "\"}";
        }
    }

    // ---- Discord IPC (named pipe) ----------------------------------------------
    private static final class Pipe {
        private final RandomAccessFile file;

        private Pipe(RandomAccessFile file) { this.file = file; }

        static Pipe open(String appId) throws IOException {
            IOException last = null;
            for (int i = 0; i < 10; i++) {
                try {
                    Pipe p = new Pipe(new RandomAccessFile("\\\\?\\pipe\\discord-ipc-" + i, "rw"));
                    try {
                        p.handshake(appId);
                        return p;
                    } catch (IOException e) {
                        last = e;
                        p.close();
                    }
                } catch (IOException e) {
                    last = e;
                }
            }
            throw last != null ? last : new IOException("no discord-ipc pipe found");
        }

        private void handshake(String appId) throws IOException {
            write(0, "{\"v\":1,\"client_id\":\"" + appId + "\"}");
            for (int i = 0; i < 4; i++) {
                Frame f = read();
                if (f.op == 3) { write(4, f.body); continue; }                       // ping -> pong
                if (f.op == 2) throw new IOException("handshake rejected: " + f.body); // close
                return;                                                                // READY
            }
        }

        void send(String json) throws IOException {
            write(1, json);
            for (int i = 0; i < 8; i++) {
                Frame f = read();
                if (f.op == 3) { write(4, f.body); continue; }
                if (f.op == 2) throw new IOException("Discord closed the connection: " + f.body);
                if (f.body.contains("\"evt\":\"ERROR\"")) log("Discord RPC rejected the presence: " + f.body);
                return;
            }
        }

        private void write(int op, String json) throws IOException {
            byte[] data = json.getBytes(StandardCharsets.UTF_8);
            ByteBuffer bb = ByteBuffer.allocate(8 + data.length).order(ByteOrder.LITTLE_ENDIAN);
            bb.putInt(op).putInt(data.length).put(data);
            file.write(bb.array());
        }

        private Frame read() throws IOException {
            byte[] head = new byte[8];
            file.readFully(head);
            ByteBuffer hb = ByteBuffer.wrap(head).order(ByteOrder.LITTLE_ENDIAN);
            int op = hb.getInt();
            int len = hb.getInt();
            if (len < 0 || len > (1 << 20)) throw new IOException("bad frame length " + len);
            byte[] body = new byte[len];
            file.readFully(body);
            return new Frame(op, new String(body, StandardCharsets.UTF_8));
        }

        void close() {
            try { file.close(); } catch (IOException ignored) { }
        }
    }

    private static final class Frame {
        final int op;
        final String body;

        Frame(int op, String body) {
            this.op = op;
            this.body = body;
        }
    }

    // ---- helpers ---------------------------------------------------------------
    private static String clip(String s) {
        if (s == null) return "  ";
        if (s.length() < 2) s = s + "  ";
        return s.length() > 128 ? s.substring(0, 128) : s;
    }

    private static String esc(String s) {
        StringBuilder b = new StringBuilder(s.length() + 8);
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) b.append(String.format("\\u%04x", (int) c));
                    else b.append(c);
            }
        }
        return b.toString();
    }

    private static long pid() {
        try {
            String n = ManagementFactory.getRuntimeMXBean().getName();
            return Long.parseLong(n.substring(0, n.indexOf('@')));
        } catch (Throwable t) {
            return 0L;
        }
    }

    private static void log(String s) {
        try {
            if (KBClientMod.logger != null) KBClientMod.logger.info("[KBClient] " + s);
        } catch (Throwable ignored) { }
    }
}
