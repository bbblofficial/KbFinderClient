package com.oryvex.kbclient.ui;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.Properties;
import net.minecraft.client.Minecraft;

public final class Settings {
    private Settings() {}

    public static final String[] FADE_NAMES = { "Off", "Fast", "Normal", "Slow" };

    public static boolean hud = true;
    public static boolean watermark = true;
    public static boolean particles = false;   // kept for compat, unused
    public static boolean aurora = false;      // kept for compat, unused
    public static boolean toasts = true;
    public static boolean customLoading = true;
    public static boolean discordRpc = true;
    public static int fade = 1;                // default: Fast
    public static int theme = 0;
    public static int density = 0;             // unused

    public static File dir() {
        File d = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!d.exists()) d.mkdirs();
        return d;
    }

    private static File file() { return new File(dir(), "settings.properties"); }

    private static int num(Properties p, String k, int def, int lo, int hi) {
        try {
            int v = Integer.parseInt(p.getProperty(k, String.valueOf(def)).trim());
            return Math.max(lo, Math.min(hi, v));
        } catch (Throwable t) { return def; }
    }

    private static boolean flag(Properties p, String k, boolean def) {
        return Boolean.parseBoolean(p.getProperty(k, String.valueOf(def)).trim());
    }

    public static void load() {
        try {
            File f = file();
            if (!f.exists()) return;
            Properties p = new Properties();
            FileInputStream in = new FileInputStream(f);
            try { p.load(in); } finally { in.close(); }
            hud = flag(p, "hud", true);
            watermark = flag(p, "watermark", true);
            toasts = flag(p, "toasts", true);
            customLoading = flag(p, "customLoading", true);
            discordRpc = flag(p, "discordRpc", true);
            fade = num(p, "fade", 1, 0, 3);
        } catch (Throwable ignored) { }
    }

    public static void save() {
        try {
            Properties p = new Properties();
            p.setProperty("hud", String.valueOf(hud));
            p.setProperty("watermark", String.valueOf(watermark));
            p.setProperty("toasts", String.valueOf(toasts));
            p.setProperty("customLoading", String.valueOf(customLoading));
            p.setProperty("discordRpc", String.valueOf(discordRpc));
            p.setProperty("fade", String.valueOf(fade));
            FileOutputStream out = new FileOutputStream(file());
            try { p.store(out, "KB Client settings"); } finally { out.close(); }
        } catch (Throwable ignored) { }
    }
}
