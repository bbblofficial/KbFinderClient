package com.oryvex.kbclient;

import com.oryvex.kbclient.ui.GuiAnalyzer;
import com.oryvex.kbclient.ui.Settings;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.lang.management.ManagementFactory;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ServerData;

/**
 * Discord Rich Presence with automatic Server Icon fetching.
 */
public final class DiscordRPC {
    public static final String APP_ID = "1554952903758716989";
    
    // Default assets (Must exist in Discord Developer Portal)
    private static final String LARGE_KEY = "oryvex"; 
    private static final String SMALL_KEY = "minecraft";

    private static final long MIN_GAP_MS = 4000L;
    private static final long RETRY_MS = 10000L;
    private static final boolean WINDOWS = System.getProperty("os.name", "").toLowerCase().contains("win");
    private static final long PID = pid();
    
    private static volatile boolean active;
    private static volatile int generation;
    private static volatile Activity pending;
    private static Thread worker;
    private static int ticks;
    
    // State tracking
    private static String curKey = "menu";
    private static long curStart;
    private static String lastServerIP = "";

    private DiscordRPC() {}

    // ---- Public API ------------------------------------------------------------
    public static synchronized void start() {
        if (!Settings.discordRpc || active) return;
        if (!WINDOWS) {
            log("Discord RPC: Windows only, disabled");
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

    public static synchronized void stop() {
        if (!active) return;
        active = false;
        generation++;
        if (worker != null) worker.interrupt();
    }

    public static void apply() {
        if (Settings.discordRpc) start(); else stop();
    }

    /** Called every client tick (main thread) */
    public static void tick() {
        if (!active) return;
        if (++ticks < 20) return; // Update every second
        ticks = 0;
        
        try {
            Minecraft mc = Minecraft.getMinecraft();
            boolean analyzing = mc.currentScreen instanceof GuiAnalyzer;
            String key, details, state;

            if (mc.theWorld == null) {
                key = "menu";
                details = "In the menus";
                state = "KB Client " + KBClientMod.VERSION;
                lastServerIP = "";
            } else if (mc.isSingleplayer()) {
                key = "sp";
                details = analyzing ? "Analyzing knockback" : "Playing Singleplayer";
                String world = "world";
                try { 
                    if (mc.getIntegratedServer() != null) {
                        world = mc.getIntegratedServer().getWorldName();
                    } 
                } catch (Throwable ignored) { }
                state = "World: " + world;
                lastServerIP = "";
            } else {
                ServerData sd = mc.getCurrentServerData();
                String ip = (sd != null && sd.serverIP != null) ? sd.serverIP : "unknown";
                String name = (sd != null && sd.serverName != null) ? sd.serverName : ip;
                
                String cacheIp = ip.contains(":") && !ip.endsWith(":25565") ? ip : ip.split(":")[0];
                
                key = "mp:" + cacheIp;
                details = analyzing ? "Analyzing knockback" : "Playing on " + name;
                state = ip;
                
                if (!cacheIp.equalsIgnoreCase(lastServerIP) && !"unknown".equals(cacheIp)) {
                    lastServerIP = cacheIp;
                    fetchServerIcon(cacheIp);
                }
            }

            if (!key.equals(curKey)) {
                curKey = key;
                curStart = System.currentTimeMillis() / 1000L;
            }
            
            pending = new Activity(details, state, curStart);
        } catch (Throwable ignored) { }
    }

    // ---- Worker ----------------------------------------------------------------
    private static void loop(int gen) {
        Pipe pipe = null;
        String sent = null;
        long lastSend = 0L;
        boolean warned = false;
        
        try {
            while (generation == gen && active) {
                try {
                    if (pipe == null) {
                        pipe = Pipe.open(APP_ID);
                        sent = null;
                        warned = false;
                        log("Connected to Discord IPC");
                    }
                    
                    Activity a = pending;
                    long now = System.currentTimeMillis();
                    
                    if (a != null && !a.sig().equals(sent) && (now - lastSend >= MIN_GAP_MS)) {
                        pipe.send(a.json());
                        sent = a.sig();
                        lastSend = now;
                    }
                    
                    Thread.sleep(1000L);
                } catch (InterruptedException e) {
                    break;
                } catch (Exception e) {
                    if (pipe != null) { 
                        pipe.close(); 
                        pipe = null; 
                    }
                    if (!warned) {
                        log("Discord not reachable (" + e.getMessage() + "), retrying...");
                        warned = true;
                    }
                    Thread.sleep(RETRY_MS);
                }
            }
        } catch (InterruptedException ignored) {
        } finally {
            if (pipe != null) {
                try { pipe.send(Activity.clearJson()); } catch (Throwable ignored) { }
                pipe.close();
            }
        }
    }

    // ---- Data Classes ----------------------------------------------------------
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
                + "\"assets\":{"
                    + "\"large_image\":\"" + LARGE_KEY + "\","
                    + "\"large_text\":\"" + esc("KB Client " + KBClientMod.VERSION) + "\","
                    + "\"small_image\":\"" + SMALL_KEY + "\","
                    + "\"small_text\":\"Minecraft 1.8.9\""
                + "}"
            + "}},\"nonce\":\"" + UUID.randomUUID() + "\"}";
        }
        
        static String clearJson() {
            return "{\"cmd\":\"SET_ACTIVITY\",\"args\":{\"pid\":" + PID + "},\"nonce\":\"" + UUID.randomUUID() + "\"}";
        }
    }

    // ---- Helpers ---------------------------------------------------------------
    private static String clip(String s) {
        if (s == null || s.trim().isEmpty()) return "  ";
        s = s.trim();
        return s.length() > 128 ? s.substring(0, 128) : s;
    }

    private static String esc(String s) {
        if (s == null) return "";
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
            int at = n.indexOf('@');
            return at > 0 ? Long.parseLong(n.substring(0, at)) : 1234L;
        } catch (Throwable t) { 
            return 1234L; 
        }
    }

    private static void log(String s) {
        try { 
            if (KBClientMod.logger != null) KBClientMod.logger.info("[KB-RPC] " + s); 
        } catch (Throwable ignored) { }
    }
    
    private static void fetchServerIcon(final String ip) {
        Thread t = new Thread(() -> {
            try {
                URL url = new URL("https://api.mc-heads.net/favicon/" + ip);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KBClient/1.0");
                conn.setConnectTimeout(3000);
                conn.setReadTimeout(3000);
                conn.setRequestMethod("GET");
                
                if (conn.getResponseCode() == 200) {
                    File dir = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
                    if (!dir.exists()) dir.mkdirs();
                    
                    File outFile = new File(dir, "server-icon.png");
                    try (InputStream in = conn.getInputStream();
                         FileOutputStream out = new FileOutputStream(outFile)) {
                        byte[] buffer = new byte[4096];
                        int bytesRead;
                        while ((bytesRead = in.read(buffer)) != -1) {
                            out.write(buffer, 0, bytesRead);
                        }
                    }
                    log("Server icon saved for: " + ip);
                }
            } catch (Exception ignored) { }
        }, "KB-IconFetcher");
        t.setDaemon(true);
        t.start();
    }
    
    // ---- Discord IPC (Named Pipe) --------------------------------------------
    private static final class Pipe {
        private final RandomAccessFile file;
        
        private Pipe(RandomAccessFile file) { 
            this.file = file; 
        }
        
        static Pipe open(String appId) throws IOException {
            for (int i = 0; i < 10; i++) {
                String pipePath = "\\\\.\\pipe\\discord-ipc-" + i;
                RandomAccessFile f = null;
                try {
                    f = new RandomAccessFile(pipePath, "rw");
                    Pipe p = new Pipe(f);
                    p.handshake(appId);
                    return p;
                } catch (IOException e) {
                    if (f != null) {
                        try { f.close(); } catch (IOException ignored) {}
                    }
                }
            }
            throw new IOException("Discord client not detected on local named pipes");
        }
        
        private void handshake(String appId) throws IOException {
            write(0, "{\"v\":1,\"client_id\":\"" + appId + "\"}");
            // Wait for Opcode 1 (FRAME) confirming READY
            for (int i = 0; i < 8; i++) {
                Frame f = read();
                if (f.op == 1) {
                    return; // Ready
                } else if (f.op == 3) {
                    write(4, f.body); // Ping -> Pong
                } else if (f.op == 2) {
                    throw new IOException("Discord rejected connection");
                }
            }
            throw new IOException("Handshake timeout without READY event");
        }
        
        String send(String json) throws IOException {
            write(1, json);
            for (int i = 0; i < 8; i++) {
                Frame f = read();
                if (f.op == 3) {
                    write(4, f.body);
                    continue;
                }
                if (f.op == 2) throw new IOException("Discord pipe closed");
                return f.body;
            }
            return "";
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
            if (len < 0 || len > (1 << 20)) throw new IOException("Invalid packet length: " + len);
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
}