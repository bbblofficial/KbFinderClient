
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
    public static boolean particles = true;
    public static boolean aurora = true;
    public static boolean toasts = true;
    public static boolean customLoading = true;
    public static boolean discordRpc = true;
    public static int fade = 2;
    public static int theme = 0;
    /** particle density 0..100 */
    public static int density = 60;

    public static File dir() {
        File dir = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    private static File file() { return new File(dir(), "settings.properties"); }

    private static int num(Properties p, String k, int def, int lo, int hi) {
        try {
            int v = Integer.parseInt(p.getProperty(k, String.valueOf(def)).trim());
            return Math.max(lo, Math.min(hi, v));
        } catch (Throwable t) {
            return def;
        }
    }

    private static boolean flag(Properties p, String k, boolean def) {
        return Boolean.parseBoolean(p.getProperty(k, String.valueOf(def)).trim());
    }

    public static void resetDefaults() {
        hud = true; watermark = true; particles = true; aurora = true; toasts = true;
        customLoading = true; discordRpc = true; fade = 2; theme = 0; density = 60;
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
            particles = flag(p, "particles", true);
            aurora = flag(p, "aurora", true);
            toasts = flag(p, "toasts", true);
            customLoading = flag(p, "customLoading", true);
            discordRpc = flag(p, "discordRpc", true);
            fade = num(p, "fade", 2, 0, 3);
            theme = num(p, "theme", 0, 0, Theme.THEME_NAMES.length - 1);
            density = num(p, "density", 60, 0, 100);
        } catch (Throwable ignored) { }
    }

    public static void save() {
        try {
            Properties p = new Properties();
            p.setProperty("hud", String.valueOf(hud));
            p.setProperty("watermark", String.valueOf(watermark));
            p.setProperty("particles", String.valueOf(particles));
            p.setProperty("aurora", String.valueOf(aurora));
            p.setProperty("toasts", String.valueOf(toasts));
            p.setProperty("customLoading", String.valueOf(customLoading));
            p.setProperty("discordRpc", String.valueOf(discordRpc));
            p.setProperty("fade", String.valueOf(fade));
            p.setProperty("theme", String.valueOf(theme));
            p.setProperty("density", String.valueOf(density));
            FileOutputStream out = new FileOutputStream(file());
            try { p.store(out, "KB Client settings"); } finally { out.close(); }
        } catch (Throwable ignored) { }
    }
}
