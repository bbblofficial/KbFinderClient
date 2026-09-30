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
    public static boolean particles = true;
    public static boolean toasts = true;
    public static boolean customLoading = true;
    public static int fade = 2;

    private static File file() {
        File dir = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!dir.exists()) dir.mkdirs();
        return new File(dir, "settings.properties");
    }

    public static void load() {
        try {
            File f = file();
            if (!f.exists()) return;
            Properties p = new Properties();
            FileInputStream in = new FileInputStream(f);
            try { p.load(in); } finally { in.close(); }
            hud = Boolean.parseBoolean(p.getProperty("hud", "true"));
            particles = Boolean.parseBoolean(p.getProperty("particles", "true"));
            toasts = Boolean.parseBoolean(p.getProperty("toasts", "true"));
            customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));
            fade = Math.max(0, Math.min(3, Integer.parseInt(p.getProperty("fade", "2"))));
        } catch (Throwable ignored) { }
    }

    public static void save() {
        try {
            Properties p = new Properties();
            p.setProperty("hud", String.valueOf(hud));
            p.setProperty("particles", String.valueOf(particles));
            p.setProperty("toasts", String.valueOf(toasts));
            p.setProperty("customLoading", String.valueOf(customLoading));
            p.setProperty("fade", String.valueOf(fade));
            FileOutputStream out = new FileOutputStream(file());
            try { p.store(out, "KB Client settings"); } finally { out.close(); }
        } catch (Throwable ignored) { }
    }
}
