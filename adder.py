#!/usr/bin/env python3
"""
adder.py - adds Discord Rich Presence ("Playing KB Client") to the KB Client mod.

Put this file in the project root (next to build.gradle) and run:

    python adder.py              apply all changes
    python adder.py --dry-run    show what would change, write nothing
    python adder.py --undo       restore the files from the last adder.py run

What it does
  * creates  src/main/java/com/oryvex/kbclient/DiscordRPC.java
        - pure Java, NO extra library, nothing to change in build.gradle
        - talks to the Discord desktop app over its local IPC pipe (Windows)
  * patches  KBClientMod.java   -> starts the presence, updates it every second
  * patches  ui/Settings.java   -> new saved option  discordRpc
  * patches  ui/GuiKbOptions.java -> new "Discord Rich Presence" toggle
  * patches  README.md          -> short note

Backups go to .fixer_backup/<timestamp>_adder/ (same folder your fixer uses).
Running it twice is safe: already-patched files are skipped.
"""

import argparse
import os
import shutil
import sys
import time

APP_ID = "1554952903758716989"

PKG = os.path.join("src", "main", "java", "com", "oryvex", "kbclient")
F_MOD = os.path.join(PKG, "KBClientMod.java")
F_SET = os.path.join(PKG, "ui", "Settings.java")
F_GUI = os.path.join(PKG, "ui", "GuiKbOptions.java")
F_RPC = os.path.join(PKG, "DiscordRPC.java")
F_README = "README.md"

BACKUP_DIR = ".fixer_backup"
MANIFEST = "adder_manifest.txt"
MARKER = "Added by adder.py"

# --------------------------------------------------------------------------
# DiscordRPC.java  (@@APP_ID@@ is replaced with the application id)
# --------------------------------------------------------------------------
JAVA_RPC = r'''package com.oryvex.kbclient;

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
    public static final String APP_ID = "@@APP_ID@@";

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
'''

README_SECTION = """
## Discord Rich Presence
KB Client shows a "Playing KB Client" status in Discord (menus / singleplayer world /
server address, with an elapsed timer). Toggle it in KB Client Options ->
"Discord Rich Presence". Needs the Discord desktop app running (Windows).
Art assets `oryvex` and `minecraft` (see `discord_assets/`) must be uploaded in the
Discord Developer Portal -> Rich Presence -> Art Assets.
"""


# --------------------------------------------------------------------------
# small text-patching toolkit (keeps each file's original line endings)
# --------------------------------------------------------------------------
class Doc:
    def __init__(self, path):
        self.path = path
        raw = open(path, "rb").read()
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        self.eol = "\r\n" if "\r\n" in text else "\n"
        self.lines = text.replace("\r\n", "\n").split("\n")
        self._orig = list(self.lines)

    def text(self):
        return "\n".join(self.lines)

    def changed(self):
        return self.lines != self._orig

    def save(self):
        data = self.eol.join(self.lines).encode("utf-8")
        if self.bom:
            data = b"\xef\xbb\xbf" + data
        with open(self.path, "wb") as f:
            f.write(data)

    def snapshot(self):
        return list(self.lines)

    def restore(self, snap):
        self.lines = snap

    def _find(self, pred):
        for i, ln in enumerate(self.lines):
            if pred(ln):
                return i
        return -1

    def insert_after(self, anchor, new, prefix=False):
        """insert `new` (same indent) after the first line equal to / starting with `anchor`"""
        i = self._find(lambda l: l.strip().startswith(anchor) if prefix else l.strip() == anchor)
        if i < 0:
            return False
        ln = self.lines[i]
        indent = ln[: len(ln) - len(ln.lstrip())]
        self.lines.insert(i + 1, indent + new)
        return True

    def replace_in_line(self, contains, old, new):
        i = self._find(lambda l: contains in l and old in l)
        if i < 0:
            return False
        self.lines[i] = self.lines[i].replace(old, new, 1)
        return True


# --------------------------------------------------------------------------
# patches - each returns (status, message); status: ok | skip | fail
# --------------------------------------------------------------------------
def patch_mod(d):
    if "DiscordRPC" in d.text():
        return "skip", "already patched"
    snap = d.snapshot()
    a = d.insert_after("installLoading();", "DiscordRPC.start();")
    b = d.insert_after("tracker.tick();", "DiscordRPC.tick();")
    if not (a and b):
        d.restore(snap)
        return "fail", "could not find installLoading(); / tracker.tick(); in KBClientMod.java"
    return "ok", "start() in init(), tick() in onTick()"


def patch_settings(d):
    if "discordRpc" in d.text():
        return "skip", "already patched"
    snap = d.snapshot()
    ok = (
        d.insert_after("public static boolean customLoading = true;", "public static boolean discordRpc = true;")
        and d.insert_after('customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));',
                           'discordRpc = Boolean.parseBoolean(p.getProperty("discordRpc", "true"));')
        and d.insert_after('p.setProperty("customLoading", String.valueOf(customLoading));',
                           'p.setProperty("discordRpc", String.valueOf(discordRpc));')
    )
    if not ok:
        d.restore(snap)
        return "fail", "Settings.java does not look like expected"
    return "ok", "added option discordRpc (load/save)"


def patch_gui(d):
    if "discordRpc" in d.text():
        return "skip", "already patched"
    snap = d.snapshot()
    ok = True
    ok &= d.replace_in_line("UiButton bHud", "bFade;", "bFade, bDisc;")
    ok &= d.replace_in_line("cardH =", "7 * (bh + gap)", "8 * (bh + gap)")
    ok &= d.replace_in_line("int y =", "Math.max(58, this.height / 2 - 78)", "Math.max(54, this.height / 2 - 93)")
    ok &= d.insert_after(
        "bFade = new UiButton(5,",
        'bDisc = new UiButton(8, cx - bw / 2, y + 5 * (bh + gap), bw, bh, "Discord Rich Presence")'
        ".style(UiButton.TOGGLE).delay(285);",
        prefix=True,
    )
    ok &= d.insert_after("this.buttonList.add(bFade);", "this.buttonList.add(bDisc);")
    # shift the two bottom buttons down by one row (Done first, then the gear button)
    ok &= d.replace_in_line('"Done"', "6 * (bh + gap) + 8", "7 * (bh + gap) + 8")
    ok &= d.replace_in_line('"Minecraft Options..."', "5 * (bh + gap) + 8", "6 * (bh + gap) + 8")
    ok &= d.insert_after("bLoad.on = Settings.customLoading;", "bDisc.on = Settings.discordRpc;")
    ok &= d.insert_after(
        "case 4:",
        "case 8: Settings.discordRpc = !Settings.discordRpc; com.oryvex.kbclient.DiscordRPC.apply(); break;",
        prefix=True,
    )
    if not ok:
        d.restore(snap)
        return "fail", "GuiKbOptions.java layout differs from what adder.py expects"
    return "ok", 'added "Discord Rich Presence" toggle to the Options screen'


def patch_readme(d):
    if "Discord Rich Presence" in d.text():
        return "skip", "already patched"
    d.lines = d.text().rstrip("\n").split("\n") + README_SECTION.rstrip("\n").split("\n") + [""]
    return "ok", "added a README section"


# --------------------------------------------------------------------------
def info(tag, msg):
    print("  [%s] %s" % (tag, msg))


def find_root(arg):
    root = os.path.abspath(arg) if arg else os.path.dirname(os.path.abspath(__file__))
    if not os.path.isfile(os.path.join(root, F_MOD)):
        print("ERROR: %s not found.\n"
              "Put adder.py in the project root (next to build.gradle) or pass the path:\n"
              "    python adder.py \"C:\\path\\to\\KnockbackClientMod\"" % F_MOD)
        sys.exit(1)
    return root


def do_undo(root):
    base = os.path.join(root, BACKUP_DIR)
    runs = sorted(n for n in (os.listdir(base) if os.path.isdir(base) else []) if n.endswith("_adder"))
    if not runs:
        print("Nothing to undo (no *_adder backup found in %s)." % BACKUP_DIR)
        return
    run = os.path.join(base, runs[-1])
    print("Undoing %s" % runs[-1])
    with open(os.path.join(run, MANIFEST), encoding="utf-8") as f:
        entries = [ln.strip() for ln in f if ln.strip()]
    for e in entries:
        kind, rel = e[0], e[2:]
        target = os.path.join(root, rel.replace("/", os.sep))
        if kind == "M":
            shutil.copy2(os.path.join(run, rel.replace("/", os.sep)), target)
            info("restored", rel)
        elif kind == "C":
            if os.path.isfile(target):
                os.remove(target)
            info("removed", rel)
    os.rename(run, run + "_undone")
    print("Done.")


def main():
    ap = argparse.ArgumentParser(description="Add Discord Rich Presence to KB Client")
    ap.add_argument("project", nargs="?", help="project root (default: folder of adder.py)")
    ap.add_argument("--dry-run", action="store_true", help="show changes, write nothing")
    ap.add_argument("--undo", action="store_true", help="restore files from the last adder.py run")
    ap.add_argument("--app-id", default=APP_ID, help="Discord application id (default: %s)" % APP_ID)
    args = ap.parse_args()

    root = find_root(args.project)
    print("Project: %s" % root)
    if args.undo:
        do_undo(root)
        return

    p_mod = os.path.join(root, F_MOD)
    p_set = os.path.join(root, F_SET)
    p_gui = os.path.join(root, F_GUI)
    p_rpc = os.path.join(root, F_RPC)
    p_readme = os.path.join(root, F_README)

    if not os.path.isfile(p_set):
        print("ERROR: %s not found." % F_SET)
        sys.exit(1)

    mod, sett = Doc(p_mod), Doc(p_set)
    gui = Doc(p_gui) if os.path.isfile(p_gui) else None
    readme = Doc(p_readme) if os.path.isfile(p_readme) else None

    print("Patching:")
    results = {}
    results["mod"] = patch_mod(mod)
    results["set"] = patch_settings(sett)
    results["gui"] = patch_gui(gui) if gui else ("fail", "GuiKbOptions.java not found")
    results["readme"] = patch_readme(readme) if readme else ("skip", "no README.md")

    labels = {"mod": "KBClientMod.java", "set": "Settings.java", "gui": "GuiKbOptions.java", "readme": "README.md"}
    for k in ("mod", "set", "gui", "readme"):
        st, msg = results[k]
        info(st.upper(), "%s - %s" % (labels[k], msg))

    # KBClientMod + Settings are required (DiscordRPC.java uses both)
    for k in ("mod", "set"):
        if results[k][0] == "fail":
            print("\nAborted: nothing was written. Send me the current %s and I'll adjust adder.py." % labels[k])
            sys.exit(1)

    # the options GUI needs Settings.discordRpc; if Settings was NOT patched now nor before, drop the GUI patch
    if results["gui"][0] == "fail":
        print("  note: Options toggle skipped - Discord RPC still works (it is on by default).")

    java = JAVA_RPC.replace("@@APP_ID@@", args.app_id)
    if mod.eol == "\r\n":
        java = java.replace("\n", "\r\n")
    rpc_exists = os.path.isfile(p_rpc)
    rpc_same = rpc_exists and open(p_rpc, "rb").read().decode("utf-8-sig") == java
    if rpc_same:
        info("SKIP", "DiscordRPC.java - already up to date")
    else:
        info("OK", "DiscordRPC.java - %s" % ("replaced" if rpc_exists else "created"))

    # collect what changes on disk
    to_write = [d for d in (mod, sett, gui, readme) if d is not None and d.changed()]
    if not to_write and rpc_same:
        print("\nNothing to do - everything is already in place.")
        return
    if args.dry_run:
        print("\nDry run: no files written.")
        return

    # backup
    run = os.path.join(root, BACKUP_DIR, time.strftime("%Y%m%d_%H%M%S") + "_adder")
    manifest = []

    def backup(path):
        rel = os.path.relpath(path, root)
        dst = os.path.join(run, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(path, dst)
        manifest.append("M " + rel.replace(os.sep, "/"))

    for d in to_write:
        backup(d.path)
    if rpc_exists and not rpc_same:
        backup(p_rpc)
    if not rpc_exists:
        manifest.append("C " + os.path.relpath(p_rpc, root).replace(os.sep, "/"))

    # write
    for d in to_write:
        d.save()
    if not rpc_same:
        os.makedirs(os.path.dirname(p_rpc), exist_ok=True)
        with open(p_rpc, "wb") as f:
            f.write(java.encode("utf-8"))

    os.makedirs(run, exist_ok=True)
    with open(os.path.join(run, MANIFEST), "w", encoding="utf-8") as f:
        f.write("\n".join(manifest) + "\n")

    print("\nDone. Backup: %s" % os.path.relpath(run, root))
    print("""
Next steps
  1. Discord Developer Portal -> your app (%s) -> Rich Presence -> Art Assets:
     upload discord_assets/oryvex.png   as  "oryvex"
     upload discord_assets/minecraft.png as  "minecraft"
     (images can take a few minutes to appear)
  2. The text after "Playing ..." is the APPLICATION NAME from the portal.
  3. Discord desktop must be running, and Settings -> Activity Privacy ->
     "Share my activity" must be on.
  4. Build:  gradlew build   (no build.gradle changes needed)
  5. Undo anytime:  python adder.py --undo
""" % args.app_id)


if __name__ == "__main__":
    main()