package com.oryvex.kbclient;

import com.oryvex.kbclient.ui.GuiAnalyzer;
import com.oryvex.kbclient.ui.Settings;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.lang.management.ManagementFactory;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ServerData;

/**
 * Discord Rich Presence with dynamic server info fetching.
 */
public final class DiscordRPC {
    // Application ID from your Discord Developer Portal
    public static final String APP_ID = "1554952903758716989"; 
    
    // Default assets (must be uploaded in Discord Dev Portal)
    private static final String DEFAULT_LARGE_KEY = "oryvex"; 
    private static final String DEFAULT_SMALL_KEY = "minecraft";

    private static final long MIN_GAP_MS = 5000L;
    private static final long RETRY_MS = 10000L;
    private static final boolean WINDOWS = System.getProperty("os.name", "").toLowerCase().contains("win");
    private static final long PID = pid();
    
    private static volatile boolean active;
    private static volatile int generation;
    private static volatile Activity pending;
    private static Thread worker;
    private static int ticks;
    
    // Cache for server icons/info to avoid spamming API
    private static final Map<String, ServerInfo> infoCache = new HashMap<>();
    private static String curKey = "menu";
    private static long curStart;

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
        pending = new Activity("In the menus", "KB Client " + KBClientMod.VERSION, curStart, DEFAULT_LARGE_KEY, DEFAULT_SMALL_KEY);
        
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
            String key, details, state, largeImg, smallImg;

            if (mc.theWorld == null) {
                key = "menu";
                details = "In the menus";
                state = "KB Client " + KBClientMod.VERSION;
                largeImg = DEFAULT_LARGE_KEY;
                smallImg = DEFAULT_SMALL_KEY;
            } else if (mc.isSingleplayer()) {
                key = "sp";
                details = analyzing ? "Analyzing knockback" : "Playing Singleplayer";
                String world = "world";
                try { if (mc.getIntegratedServer() != null) world = mc.getIntegratedServer().getWorldName(); } catch (Throwable ignored) { }
                state = "World: " + world;
                largeImg = DEFAULT_LARGE_KEY;
                smallImg = DEFAULT_SMALL_KEY;
            } else {
                ServerData sd = mc.getCurrentServerData();
                String ip = (sd != null) ? sd.serverIP : "unknown";
                // Normalize IP for cache key (remove port if default 25565)
                String cacheIp = ip.contains(":") && !ip.endsWith(":25565") ? ip : ip.split(":")[0];
                
                key = "mp:" + cacheIp;
                details = analyzing ? "Analyzing knockback" : "Playing on " + sd.serverName;
                
                // Fetch server info asynchronously or from cache
                ServerInfo info = getServerInfo(cacheIp);
                state = info != null && info.online ? info.motdClean : "Connecting...";
                
                // NOTE: Discord RPC requires pre-uploaded assets. 
                // We cannot dynamically upload images via IPC.
                // Strategy: Use a generic 'server' asset or fallback to default.
                // If you want specific icons, you must map them manually below or upload a generic 'globe' icon.
                largeImg = "server_icon"; // You should upload a generic server icon named 'server_icon' in Dev Portal
                smallImg = DEFAULT_SMALL_KEY;
            }

            if (!key.equals(curKey)) {
                curKey = key;
                curStart = System.currentTimeMillis() / 1000L;
            }
            
            pending = new Activity(details, state, curStart, largeImg, smallImg);
        } catch (Throwable ignored) { }
    }

    // ---- Worker ----------------------------------------------------------------
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
                        log("Connected to Discord");
                    }
                    
                    Activity a = pending;
                    long now = System.currentTimeMillis();
                    
                    if (a != null && !a.sig().equals(sent) && now - lastSend >= MIN_GAP_MS) {
                        pipe.send(a.json());
                        sent = a.sig();
                        lastSend = now;
                    }
                    Thread.sleep(1000L);
                } catch (Exception e) {
                    if (pipe != null) { pipe.close(); pipe = null; }
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
        final String details, state, largeImg, smallImg;
        final long start;
        
        Activity(String details, String state, long start, String largeImg, String smallImg) {
            this.details = details;
            this.state = state;
            this.start = start;
            this.largeImg = largeImg;
            this.smallImg = smallImg;
        }
        
        String sig() { return details + "\n" + state + "\n" + largeImg + "\n" + smallImg; }
        
        String json() {
            return "{\"cmd\":\"SET_ACTIVITY\",\"args\":{\"pid\":" + PID + ",\"activity\":{"
                + "\"details\":\"" + esc(clip(details)) + "\","
                + "\"state\":\"" + esc(clip(state)) + "\","
                + "\"timestamps\":{\"start\":" + start + "},"
                + "\"assets\":{"
                    + "\"large_image\":\"" + largeImg + "\","
                    + "\"large_text\":\"" + esc("KB Client " + KBClientMod.VERSION) + "\","
                    + "\"small_image\":\"" + smallImg + "\","
                    + "\"small_text\":\"Minecraft 1.8.9\""
                + "}"
            + "}},\"nonce\":\"" + UUID.randomUUID() + "\"}";
        }
        
        static String clearJson() {
            return "{\"cmd\":\"SET_ACTIVITY\",\"args\":{\"pid\":" + PID + "},\"nonce\":\"" + UUID.randomUUID() + "\"}";
        }
    }

    private static final class ServerInfo {
        boolean online;
        String motdClean;
        int players;
    }

    // ---- Helpers ---------------------------------------------------------------
    private static ServerInfo getServerInfo(String ip) {
        if (infoCache.containsKey(ip)) return infoCache.get(ip);
        
        // Non-blocking check would be better, but for simplicity we do a quick sync check 
        // or return a placeholder if it takes too long. 
        // Here we use a very short timeout to avoid freezing the game.
        try {
            URL url = new URL("https://api.mcsrvstat.us/2/" + ip);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(1500);
            conn.setReadTimeout(1500);
            conn.setRequestMethod("GET");
            
            if (conn.getResponseCode() == 200) {
                BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = in.readLine()) != null) response.append(line);
                in.close();
                
                String json = response.toString();
                ServerInfo info = new ServerInfo();
                info.online = json.contains("\"online\":true");
                
                // Extract clean MOTD (simplified parsing)
                if (info.online) {
                    // Very basic JSON parsing for MOTD clean
                    int motdIdx = json.indexOf("\"motd\":{");
                    if (motdIdx > 0) {
                        int cleanIdx = json.indexOf("\"clean\":[", motdIdx);
                        if (cleanIdx > 0) {
                            int start = json.indexOf("[\"", cleanIdx) + 2;
                            int end = json.indexOf("\"]", start);
                            if (start > 1 && end > start) {
                                info.motdClean = json.substring(start, end).replace("\\n", " ");
                            }
                        }
                    }
                    // Extract player count
                    int playIdx = json.indexOf("\"players\":{");
                    if (playIdx > 0) {
                        int onlineIdx = json.indexOf("\"online\":", playIdx);
                        if (onlineIdx > 0) {
                            int numStart = onlineIdx + 9;
                            int numEnd = json.indexOf(",", numStart);
                            if (numEnd == -1) numEnd = json.indexOf("}", numStart);
                            if (numEnd > numStart) {
                                try { info.players = Integer.parseInt(json.substring(numStart, numEnd).trim()); } catch(Exception e){}
                            }
                        }
                    }
                } else {
                    info.motdClean = "Offline";
                }
                
                infoCache.put(ip, info);
                return info;
            }
        } catch (Exception e) {
            // Ignore timeouts/errors
        }
        
        ServerInfo fallback = new ServerInfo();
        fallback.online = false;
        fallback.motdClean = "Unknown Server";
        infoCache.put(ip, fallback);
        return fallback;
    }

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
        } catch (Throwable t) { return 0L; }
    }

    private static void log(String s) {
        try { if (KBClientMod.logger != null) KBClientMod.logger.info("[KB-RPC] " + s); } catch (Throwable ignored) { }
    }
    
    // ---- Discord IPC (Named Pipe) --------------------------------------------
    // [Keep the existing Pipe, Frame classes from your original code here exactly as they were]
    // ... (Copy the Pipe and Frame inner classes from your previous working version) ...
    
    private static final class Pipe {
        private static final String[] PREFIXES = { "\\\\?\\pipe\\", "\\\\.\\pipe\\" };
        private final java.io.RandomAccessFile file;
        String ready = "";
        private Pipe(java.io.RandomAccessFile file) { this.file = file; }
        static Pipe open(String appId) throws java.io.IOException {
            StringBuilder errs = new StringBuilder();
            for (int i = 0; i < 10; i++) {
                for (int k = 0; k < PREFIXES.length; k++) {
                    java.io.RandomAccessFile f;
                    try { f = new java.io.RandomAccessFile(PREFIXES[k] + "discord-ipc-" + i, "rw"); } 
                    catch (java.io.IOException e) { continue; }
                    Pipe p = new Pipe(f);
                    try { p.handshake(appId); return p; } 
                    catch (java.io.IOException e) { p.close(); }
                }
            }
            throw new java.io.IOException("no discord-ipc pipe found");
        }
        private void handshake(String appId) throws java.io.IOException {
            write(0, "{\"v\":1,\"client_id\":\"" + appId + "\"}");
            for (int i = 0; i < 4; i++) { Frame f = read(); if (f.op == 3) { write(4, f.body); continue; } if (f.op == 2) throw new java.io.IOException("rejected"); return; }
        }
        void send(String json) throws java.io.IOException { write(1, json); for (int i = 0; i < 8; i++) { Frame f = read(); if (f.op == 3) { write(4, f.body); continue; } if (f.op == 2) throw new java.io.IOException("closed"); return; } }
        private void write(int op, String json) throws java.io.IOException { byte[] data = json.getBytes(StandardCharsets.UTF_8); java.nio.ByteBuffer bb = java.nio.ByteBuffer.allocate(8 + data.length).order(java.nio.ByteOrder.LITTLE_ENDIAN); bb.putInt(op).putInt(data.length).put(data); file.write(bb.array()); }
        private Frame read() throws java.io.IOException { byte[] head = new byte[8]; file.readFully(head); java.nio.ByteBuffer hb = java.nio.ByteBuffer.wrap(head).order(java.nio.ByteOrder.LITTLE_ENDIAN); int op = hb.getInt(); int len = hb.getInt(); if (len < 0 || len > (1 << 20)) throw new java.io.IOException("bad len"); byte[] body = new byte[len]; file.readFully(body); return new Frame(op, new String(body, StandardCharsets.UTF_8)); }
        void close() { try { file.close(); } catch (java.io.IOException ignored) { } }
    }
    private static final class Frame { final int op; final String body; Frame(int op, String body) { this.op = op; this.body = body; } }
}