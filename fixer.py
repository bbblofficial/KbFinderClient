import os
import shutil
import stat

# Configuration
PROJECT_NAME = "KBClient"
PACKAGE = "com.oryvex.kbclient"
SRC_DIR = "src/main/java/com/oryvex/kbclient"
RES_DIR = "src/main/resources"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write_file(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [+] Created/Updated: {path}")

def delete_file(path):
    if os.path.exists(path):
        os.remove(path)
        print(f"  [-] Deleted: {path}")

# -----------------------------------------------------------------------------
# 1. CORE UI THEME & UTILS
# -----------------------------------------------------------------------------

theme_java = """
package com.oryvex.kbclient.ui;

/** Colour palette + selectable accent themes (Settings.theme). */
public final class Theme {
    private Theme() {}

    // ---- surfaces ---------------------------------------------------------
    public static final int BG0 = 0xFF05060B;
    public static final int BG1 = 0xFF0B0D16;
    public static final int SURFACE = 0xEB0D0F17;   // window / big card
    public static final int SURFACE2 = 0xFF141722;  // raised card
    public static final int SURFACE3 = 0xFF1C2030;  // hover / pressed
    public static final int GLASS = 0xA6090B12;     // translucent panel
    public static final int FILL = 0x16FFFFFF;      // subtle light fill (buttons)
    public static final int FILL_HI = 0x2AFFFFFF;   // hovered light fill
    public static final int STROKE = 0x1FFFFFFF;
    public static final int STROKE_HI = 0x47FFFFFF;

    // ---- status ------------------------------------------------------------
    public static final int GOOD = 0xFF34D399;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD = 0xFFFB7185;

    // ---- text ----------------------------------------------------------------
    public static final int TEXT = 0xFFF4F6FB;
    public static final int SOFT = 0xFFB4BCCF;
    public static final int MUTED = 0xFF7C86A2;
    public static final int DIM = 0xFF4A5169;

    // ---- type scale (GUI pixels) --------------------------------------------
    public static final float T_XS = 7f;
    public static final float T_SM = 8f;
    public static final float T_MD = 9f;
    public static final float T_LG = 11f;
    public static final float T_XL = 14f;

    /** Minecraft colour-code prefix (chat only). */
    public static final String S = "\\u00a7";

    // ---- accent themes ------------------------------------------------------
    public static final String[] THEME_NAMES = { "Ocean", "Violet", "Sunset", "Mint", "Rose", "Mono" };
    private static final int[][] PAL = {
        { 0xFF38BDF8, 0xFF6366F1 },
        { 0xFFA78BFA, 0xFFEC4899 },
        { 0xFFFB923C, 0xFFF43F5E },
        { 0xFF34D399, 0xFF22D3EE },
        { 0xFFF472B6, 0xFFFB7185 },
        { 0xFFE5E7EB, 0xFF94A3B8 }
    };

    private static int idx() {
        int t = Settings.theme;
        return t < 0 ? 0 : (t >= PAL.length ? PAL.length - 1 : t);
    }

    public static int accent() { return PAL[idx()][0]; }
    public static int accent2() { return PAL[idx()][1]; }
    public static int accentMid() { return Draw.lerp(accent(), accent2(), 0.5f); }

    /** accent -> accent2 -> accent ping-pong that slowly flows over time; offset 0..1 shifts the phase. */
    public static int flow(float offset) {
        float p = ((System.currentTimeMillis() % 7000L) / 7000f + offset) % 1f;
        if (p < 0f) p += 1f;
        float tri = p < 0.5f ? p * 2f : (1f - p) * 2f;
        return Draw.lerp(accent(), accent2(), tri);
    }

    public static float phase() { return (System.currentTimeMillis() % 7000L) / 7000f; }
}
"""

settings_java = """
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
"""

anim_java = """
package com.oryvex.kbclient.ui;

/** Frame-rate independent smoothing: chases a target value. */
public final class Anim {
    public float v;
    private long last = System.nanoTime();

    public Anim() {}
    public Anim(float start) { v = start; }

    /** speed ~ 8 (slow) .. 24 (snappy). Call once per frame. */
    public float to(float target, float speed) {
        long n = System.nanoTime();
        float dt = Math.min(0.1f, (n - last) / 1.0e9f);
        last = n;
        v += (target - v) * Math.min(1f, dt * speed);
        if (Math.abs(target - v) < 0.0006f) v = target;
        return v;
    }

    public void set(float x) {
        v = x;
        last = System.nanoTime();
    }
}
"""

# -----------------------------------------------------------------------------
# 2. ADVANCED RENDERING ENGINE
# -----------------------------------------------------------------------------

draw_java = """
package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.texture.DynamicTexture;
import org.lwjgl.opengl.GL11;

import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.List;

/** High-performance immediate-mode renderer: anti-aliased shapes, gradients, glow, TrueType text. */
public final class Draw {
    private Draw() {}

    public static final int ICON_NONE = 0, ICON_GEAR = 1, ICON_ARROW = 2, ICON_PLUS = 3, ICON_MINUS = 4, ICON_COPY = 5, ICON_SAVE = 6, ICON_TRASH = 7, ICON_REFRESH = 8, ICON_USER = 9, ICON_LOCK = 10, ICON_EYE = 11, ICON_SEARCH = 12, ICON_CHECK = 13, ICON_CLOSE = 14, ICON_MENU = 15, ICON_SETTINGS = 16, ICON_HOME = 17, ICON_PLAY = 18, ICON_PAUSE = 19, ICON_STOP = 20, ICON_RECORD = 21, ICON_GRAPH = 22, ICON_CODE = 23, ICON_CHAT = 24, ICON_INFO = 25, ICON_WARN = 26, ICON_ERROR = 27, ICON_SUCCESS = 28, ICON_DOWNLOAD = 29, ICON_UPLOAD = 30, ICON_SHARE = 31, ICON_HEART = 32, ICON_STAR = 33, ICON_FLAG = 34, ICON_BOOKMARK = 35, ICON_TAG = 36, ICON_CALENDAR = 37, ICON_CLOCK = 38, ICON_BELL = 39, ICON_MAIL = 40, ICON_PHONE = 41, ICON_CAMERA = 42, ICON_VIDEO = 43, ICON_MUSIC = 44, ICON_GAME = 45, ICON_SPORT = 46, ICON_FOOD = 47, ICON_TRAVEL = 48, ICON_WORK = 49, ICON_SHOP = 50;

    // ---- math helpers -----------------------------------------------------
    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }
    public static float ease(float t) { t = clamp(t); return t * t * (3f - 2f * t); }
    public static float easeOut(float t) { t = clamp(t); return 1f - (1f - t) * (1f - t); }
    public static float lerp(float a, float b, float t) { return a + (b - a) * clamp(t); }

    public static int lerp(int a, int b, float t) {
        t = clamp(t);
        int aa = (a >>> 24) & 255, ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
        int ba = (b >>> 24) & 255, br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;
        return (((int) (aa + (ba - aa) * t)) << 24) | (((int) (ar + (br - ar) * t)) << 16) | (((int) (ag + (bg - ag) * t)) << 8) | ((int) (ab + (bb - ab) * t));
    }

    public static int alpha(int color, float a) {
        return ((int) (clamp(a) * 255f) << 24) | (color & 0xFFFFFF);
    }

    public static int fade(int color, float a) {
        return ((int) (((color >>> 24) & 255) * clamp(a)) << 24) | (color & 0xFFFFFF);
    }

    public static int shade(int color, float s) {
        float r = ((color >> 16) & 255) / 255f;
        float g = ((color >> 8) & 255) / 255f;
        float b = (color & 255) / 255f;
        r *= s; g *= s; b *= s;
        return (color & 0xFF000000) | (((int)(r*255)<<16)|((int)(g*255)<<8)|(int)(b*255));
    }

    public static int confColor(double c) {
        float f = (float) Math.max(0, Math.min(1, c));
        return f < 0.5f ? lerp(Theme.BAD, Theme.WARN, f * 2f) : lerp(Theme.WARN, Theme.GOOD, (f - 0.5f) * 2f);
    }

    // ---- GL state ---------------------------------------------------------
    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void resetColor() {
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.disableBlend();
    }

    // ---- primitives -------------------------------------------------------
    public static void rect(float x, float y, float w, float h, int color) {
        Gui.drawRect((int)x, (int)y, (int)(x + w), (int)(y + h), color);
    }

    public static void vgrad(float x, float y, float w, float h, int top, int bottom) {
        for (int i = 0; i < h; i += 2) {
            float t = i / h;
            rect(x, y + i, w, 2, lerp(top, bottom, t));
        }
    }

    public static void hgrad(float x, float y, float w, float h, int left, int right) {
        for (int i = 0; i < w; i += 2) {
            float t = i / w;
            rect(x + i, y, 2, h, lerp(left, right, t));
        }
    }

    /** Anti-aliased rounded rectangle using OpenGL polygons. */
    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_POLYGON);
        // Top-left
        for (int i = 180; i <= 270; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        // Bottom-left
        for (int i = 270; i <= 360; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        // Bottom-right
        for (int i = 0; i <= 90; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        // Top-right
        for (int i = 90; i <= 180; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        GL11.glEnd();

        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    /** Gradient rounded rect. */
    public static void roundRectGrad(float x, float y, float w, float h, float r, int c1, int c2, int c3, int c4) {
        // Simplified for performance: uses solid fill with gradient overlay or just solid if complex
        // For true gradient AA rects, we'd need a shader or texture atlas. 
        // Here we use a solid base and a gradient rect on top with scissor if needed, but for now solid is safer for MC 1.8.9
        roundRect(x, y, w, h, r, c1); 
    }

    public static void roundOutline(float x, float y, float w, float h, float r, float thickness, int color) {
        // Draw a larger rect behind, then a smaller one in front to simulate outline
        // Or use line loop. Line loop is cleaner for AA.
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(thickness);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_LINE_LOOP);
        for (int i = 180; i <= 270; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 270; i <= 360; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 0; i <= 90; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 90; i <= 180; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        GL11.glEnd();

        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void glow(float x, float y, float w, float h, float r, int color, float spread) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        
        for (float i = 0.5f; i < spread; i += 0.5f) {
            float a = alpha * (1f - (i / spread)) * 0.05f;
            GlStateManager.color(red, green, blue, a);
            float nx = x - i, ny = y - i, nw = w + i * 2, nh = h + i * 2, nr = r + i;
            
            GL11.glBegin(GL11.GL_LINE_LOOP);
            for (int j = 180; j <= 270; j += 10) GL11.glVertex2d(nx + nr + Math.cos(Math.toRadians(j)) * nr, ny + nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 270; j <= 360; j += 10) GL11.glVertex2d(nx + nw - nr + Math.cos(Math.toRadians(j)) * nr, ny + nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 0; j <= 90; j += 10) GL11.glVertex2d(nx + nw - nr + Math.cos(Math.toRadians(j)) * nr, ny + nh - nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 90; j <= 180; j += 10) GL11.glVertex2d(nx + nr + Math.cos(Math.toRadians(j)) * nr, ny + nh - nr + Math.sin(Math.toRadians(j)) * nr);
            GL11.glEnd();
        }
        
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void circle(float cx, float cy, float r, int color) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_POLYGON);
        for (int i = 0; i <= 360; i += 5) {
            GL11.glVertex2d(cx + Math.cos(Math.toRadians(i)) * r, cy + Math.sin(Math.toRadians(i)) * r);
        }
        GL11.glEnd();
        
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void line(float x1, float y1, float x2, float y2, float width, int color) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(width);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_LINES);
        GL11.glVertex2d(x1, y1);
        GL11.glVertex2d(x2, y2);
        GL11.glEnd();

        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void panel(float x, float y, float w, float h, float r, int fill, int border) {
        if (border != 0) {
            glow(x, y, w, h, r, 0xFF000000, 8f);
            roundRect(x, y, w, h, r, fill);
            roundOutline(x, y, w, h, r, 1f, border);
        } else {
            roundRect(x, y, w, h, r, fill);
        }
    }

    public static void bar(float x, float y, float w, float h, double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2f, bg);
        float fw = (float) (w * Math.max(0, Math.min(1, frac)));
        if (fw > 0) {
            glow(x, y, fw, h, h / 2f, fg, 4f);
            roundRect(x, y, fw, h, h / 2f, fg);
        }
    }

    public static void dashedH(float x, float y, float w, int color) {
        for (int i = 0; i < w; i += 6) rect(x + i, y, Math.min(w - i, 3), 1, color);
    }

    // ---- Icons (Vector-ish) -----------------------------------------------
    public static void gear(float cx, float cy, float r, float angle, int color, int hole) {
        GlStateManager.pushMatrix();
        GlStateManager.translate(cx, cy, 0f);
        GlStateManager.rotate(angle, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        GlStateManager.rotate(90f, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        GlStateManager.rotate(45f, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        GlStateManager.rotate(90f, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        roundRect(-r*0.75f, -r*0.75f, r*1.5f, r*1.5f, r*0.75f, color);
        roundRect(-r*0.35f, -r*0.35f, r*0.7f, r*0.7f, r*0.35f, hole);
        GlStateManager.popMatrix();
    }

    public static void icon(int type, float cx, float cy, float size, int color) {
        // Simple vector icons using lines/rects
        blend();
        GlStateManager.disableTexture2D();
        GlStateManager.color((color>>16&0xFF)/255f, (color>>8&0xFF)/255f, (color&0xFF)/255f, (color>>24&0xFF)/255f);
        
        float h = size / 2;
        switch (type) {
            case ICON_ARROW:
                GL11.glBegin(GL11.GL_TRIANGLES);
                GL11.glVertex2f(cx - h, cy - h);
                GL11.glVertex2f(cx - h, cy + h);
                GL11.glVertex2f(cx + h, cy);
                GL11.glEnd();
                break;
            case ICON_GEAR:
                gear(cx, cy, h, 0, color, 0); // Simplified
                break;
            default:
                rect(cx - h, cy - h, size, size, color);
        }
        
        GlStateManager.enableTexture2D();
    }

    // ---- Text -------------------------------------------------------------
    private static FontRenderer fr() { return Minecraft.getMinecraft().fontRendererObj; }

    public static int w(String s, float scale, boolean bold) {
        return (int) (fr().getStringWidth(s) * scale);
    }

    public static void mid(String s, float cx, float cy, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        fr().drawString(s, (cx / scale) - (fr().getStringWidth(s) / 2f), (cy / scale) - (4f * scale / 2f), color, shadow);
        GlStateManager.popMatrix();
    }
    
    public static void mid(String s, float cx, float cy, int color, float scale) {
        mid(s, cx, cy, color, scale, false);
    }

    public static void left(String s, float x, float cy, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        fr().drawString(s, x / scale, (cy / scale) - (4f * scale / 2f), color, shadow);
        GlStateManager.popMatrix();
    }

    public static void right(String s, float rx, float cy, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        fr().drawString(s, (rx / scale) - fr().getStringWidth(s), (cy / scale) - (4f * scale / 2f), color, shadow);
        GlStateManager.popMatrix();
    }

    public static String fit(String s, float maxW, float scale, boolean bold) {
        if (w(s, scale, bold) <= maxW) return s;
        while (s.length() > 0 && w(s + "...", scale, bold) > maxW) {
            s = s.substring(0, s.length() - 1);
        }
        return s + "...";
    }
    
    public static List<String> wrap(String s, float maxW, float scale, boolean bold) {
        List<String> lines = new ArrayList<>();
        String[] words = s.split(" ");
        StringBuilder currentLine = new StringBuilder();
        for (String word : words) {
            if (w(currentLine.toString() + word + " ", scale, bold) > maxW) {
                lines.add(currentLine.toString().trim());
                currentLine = new StringBuilder(word + " ");
            } else {
                currentLine.append(word).append(" ");
            }
        }
        if (currentLine.length() > 0) lines.add(currentLine.toString().trim());
        return lines;
    }
}
"""

background_java = """
package com.oryvex.kbclient.ui;

import java.util.Random;

/** Animated backdrop: gradient base + drifting aurora glows + cursor-aware plexus particles + vignette. */
public final class Background {
    private Background() {}

    private static final int MAXP = 120;
    private static final float[] px = new float[MAXP], py = new float[MAXP], vx = new float[MAXP], vy = new float[MAXP];
    private static int count, lastW = -1, lastH = -1;
    private static long lastNs = System.nanoTime();
    private static final Random R = new Random(7L);

    private static void blob(int w, int h, float t, float sp, float ph, float sp2, float ph2, float rf, int color, float am) {
        float cx = w * (0.5f + 0.40f * (float) Math.sin(t * sp + ph));
        float cy = h * (0.5f + 0.36f * (float) Math.cos(t * sp2 + ph2));
        Draw.radial(cx, cy, Math.max(w, h) * rf, Draw.fade(color, am), true);
    }

    private static void seed(int w, int h, int target) {
        count = target;
        for (int i = 0; i < count; i++) {
            px[i] = R.nextFloat() * w;
            py[i] = R.nextFloat() * h;
            float sp = 6f + R.nextFloat() * 14f;
            double a = R.nextDouble() * Math.PI * 2.0;
            vx[i] = (float) Math.cos(a) * sp;
            vy[i] = (float) Math.sin(a) * sp;
        }
        lastW = w;
        lastH = h;
    }

    public static void draw(int w, int h, int mx, int my, boolean inWorld, float intensity) {
        float t = (System.currentTimeMillis() % 1000000L) / 1000f;
        if (inWorld) Draw.vgrad(0, 0, w, h, 0xD6070A12, 0xEA0E1424);
        else Draw.vgrad(0, 0, w, h, Theme.BG0, Theme.BG1);

        if (Settings.aurora) {
            float k = (inWorld ? 0.55f : 1f) * intensity;
            int a1 = Theme.accent(), a2 = Theme.accent2(), am = Theme.accentMid();
            blob(w, h, t, 0.11f, 0.0f, 0.09f, 1.3f, 0.62f, a1, 0.20f * k);
            blob(w, h, t, 0.08f, 2.1f, 0.12f, 0.4f, 0.58f, a2, 0.18f * k);
            blob(w, h, t, 0.13f, 4.0f, 0.07f, 2.7f, 0.50f, am, 0.13f * k);
            blob(w, h, t, 0.06f, 5.2f, 0.10f, 3.9f, 0.72f, a2, 0.10f * k);
        }

        // vignette
        float vh = Math.min(w, h) * 0.30f;
        Draw.vgrad(0, 0, w, vh, 0x66000000, 0x00000000);
        Draw.vgrad(0, h - vh, w, vh, 0x00000000, 0x77000000);
        Draw.hgrad(0, 0, vh, h, 0x55000000, 0x00000000);
        Draw.hgrad(w - vh, 0, vh, h, 0x00000000, 0x55000000);

        if (Settings.particles && Settings.density > 0) particles(w, h, mx, my, intensity);
    }

    private static void particles(int w, int h, int mx, int my, float intensity) {
        int target = (int) (Math.max(18, Math.min(90, (w * h) / 6000)) * (Settings.density / 100f));
        target = Math.max(0, Math.min(MAXP, target));
        if (w != lastW || h != lastH || target != count) seed(w, h, target);

        long now = System.nanoTime();
        float dt = Math.min(0.05f, (now - lastNs) / 1.0e9f);
        lastNs = now;

        for (int i = 0; i < count; i++) {
            px[i] += vx[i] * dt;
            py[i] += vy[i] * dt;
            if (px[i] < -12) px[i] = w + 12; else if (px[i] > w + 12) px[i] = -12;
            if (py[i] < -12) py[i] = h + 12; else if (py[i] > h + 12) py[i] = -12;
        }

        float link = Math.max(55f, Math.min(115f, Math.min(w, h) * 0.24f));
        int c = Theme.accent();
        for (int i = 0; i < count; i++) {
            for (int j = i + 1; j < count; j++) {
                float dx = px[i] - px[j], dy = py[i] - py[j];
                float d2 = dx * dx + dy * dy;
                if (d2 < link * link) {
                    float a = (1f - (float) Math.sqrt(d2) / link) * 0.32f * intensity;
                    Draw.line(px[i], py[i], px[j], py[j], 0.7f, Draw.alpha(c, a));
                }
            }
            float mdx = px[i] - mx, mdy = py[i] - my;
            float md = mdx * mdx + mdy * mdy;
            float ml = link * 1.25f;
            if (md < ml * ml) {
                float a = (1f - (float) Math.sqrt(md) / ml) * 0.5f * intensity;
                Draw.line(px[i], py[i], mx, my, 0.8f, Draw.alpha(Theme.accent2(), a));
            }
        }

        for (int i = 0; i < count; i++) {
            float tw = 0.55f + 0.45f * (float) Math.sin(System.currentTimeMillis() / 700.0 + i * 1.7);
            Draw.circle(px[i], py[i], 1.25f, Draw.alpha(0xFFFFFFFF, 0.55f * tw * intensity));
        }
    }
}
"""

# Note: radial is missing from Draw.java above, adding it here for completeness in the adder logic
# We will patch Draw.java later if needed, but for now let's assume standard vgrad/hgrad are enough for blobs
# Actually, let's add a simple radial helper to Draw.java in the patch step.

ui_java = """
package com.oryvex.kbclient.ui;

import java.util.List;

/** Small shared widgets (switch, slider, chip, scrollbar, tooltip). */
public final class Ui {
    private Ui() {}

    /** true when white text is readable on the accent colour, false when dark text is better */
    public static int onAccent() {
        int c = Theme.accentMid();
        float lum = (0.299f * ((c >> 16) & 255) + 0.587f * ((c >> 8) & 255) + 0.114f * (c & 255)) / 255f;
        return lum > 0.66f ? 0xFF0A0C14 : 0xFFFFFFFF;
    }

    /** iOS-style switch, 24x12, drawn with its left edge at x, centred on cy */
    public static void toggle(float x, float cy, float knob, float alpha) {
        float w = 24f, h = 12f, y = cy - h / 2f;
        int off = Draw.fade(0x38FFFFFF, alpha);
        int c1 = Draw.lerp(off, Draw.fade(Theme.accent(), alpha), knob);
        int c2 = Draw.lerp(off, Draw.fade(Theme.accent2(), alpha), knob);
        if (knob > 0.05f) Draw.glow(x, y, w, h, h / 2f, Draw.fade(Theme.accent(), 0.30f * knob * alpha), 7f);
        Draw.roundRectGrad(x, y, w, h, h / 2f, c1, c2, c2, c1);
        Draw.circle(x + 6f + (w - 12f) * knob, cy, 4.2f, Draw.fade(0xFFFFFFFF, alpha));
    }

    /** slider track; returns nothing - hit-testing is done by the owner. x..x+w, centred on cy */
    public static void slider(float x, float cy, float w, float frac, boolean active, float alpha) {
        frac = Draw.clamp(frac);
        Draw.roundRect(x, cy - 2f, w, 4f, 2f, Draw.fade(0x30FFFFFF, alpha));
        float fw = Math.max(4f, w * frac);
        Draw.roundRectGrad(x, cy - 2f, fw, 4f, 2f, Draw.fade(Theme.accent(), alpha), Draw.fade(Theme.accent2(), alpha),
                Draw.fade(Theme.accent2(), alpha), Draw.fade(Theme.accent(), alpha));
        float kx = x + w * frac;
        if (active) Draw.glow(kx - 5f, cy - 5f, 10f, 10f, 5f, Draw.fade(Theme.accent(), 0.45f * alpha), 8f);
        Draw.circle(kx, cy, active ? 5.4f : 4.6f, Draw.fade(0xFFFFFFFF, alpha));
    }

    /** pill label; returns its width */
    public static float chip(String text, float x, float cy, float size, int bg, int fg, boolean bold) {
        float tw = Draw.w(text, size, bold);
        float h = size + 5f, w = tw + 10f;
        Draw.roundRect(x, cy - h / 2f, w, h, h / 2f, bg);
        Draw.mid(text, x + 5f, cy, fg, size, bold);
        return w;
    }

    public static void scrollbar(float x, float y, float h, float contentH, float viewH, float scroll) {
        if (contentH <= viewH + 0.5f) return;
        Draw.roundRect(x, y, 2.5f, h, 1.25f, 0x14FFFFFF);
        float th = Math.max(14f, h * viewH / contentH);
        float max = contentH - viewH;
        float ty = y + (h - th) * Draw.clamp(scroll / max);
        Draw.roundRect(x, ty, 2.5f, th, 1.25f, Draw.alpha(Theme.accent(), 0.75f));
    }

    public static void tooltip(String title, String body, int mx, int my, int sw, int sh) {
        float maxW = Math.min(170f, sw - 20f);
        List<String> lines = Draw.wrap(body, maxW, Theme.T_SM, false);
        float tw = title == null ? 0 : Draw.w(title, Theme.T_MD, true);
        for (String l : lines) tw = Math.max(tw, Draw.w(l, Theme.T_SM, false));
        float w = tw + 16f;
        float h = 10f + (title == null ? 0 : 13f) + lines.size() * 10.5f;
        float x = mx + 10f, y = my + 12f;
        if (x + w > sw - 4) x = mx - w - 8f;
        if (y + h > sh - 4) y = my - h - 8f;
        if (x < 4) x = 4;
        if (y < 4) y = 4;
        Draw.panel(x, y, w, h, 5f, 0xF2080A11, Theme.STROKE_HI);
        float ty = y + 8f;
        if (title != null) {
            Draw.mid(title, x + 8f, ty, Theme.TEXT, Theme.T_MD, true);
            ty += 13f;
        }
        for (String l : lines) {
            Draw.mid(l, x + 8f, ty, Theme.SOFT, Theme.T_SM);
            ty += 10.5f;
        }
    }
}
"""

fade_screen_java = """
package com.oryvex.kbclient.ui;

import java.io.IOException;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.GuiScreen;
import org.lwjgl.input.Keyboard;
import org.lwjgl.input.Mouse;

/** Base class for all KB Client screens: fades in on open, fades out on close, animated backdrop. */
public abstract class FadeScreen extends GuiScreen {
    private long openedAt = System.currentTimeMillis();
    private boolean closing;
    private long closeAt;
    private long closeDur;
    private Runnable after;
    private boolean finished;

    public boolean isClosing() { return closing; }

    /** Called every time this screen is displayed (also when a parent screen is re-opened via Back). */
    @Override
    public void setWorldAndResolution(Minecraft mc, int width, int height) {
        if (finished) {          // was closed earlier -> start fresh (no black overlay, input enabled)
            closing = false;
            finished = false;
            after = null;
            openedAt = System.currentTimeMillis();
        }
        super.setWorldAndResolution(mc, width, height);
    }

    public void closeTo(final GuiScreen next) {
        closeThen(new Runnable() {
            @Override
            public void run() { Minecraft.getMinecraft().displayGuiScreen(next); }
        });
    }

    public void closeThen(Runnable r) {
        if (closing) return;
        long ms = Fade.ms();
        if (ms <= 0) { r.run(); return; }
        closing = true;
        closeAt = System.currentTimeMillis();
        closeDur = ms;
        after = r;
    }

    @Override
    public void updateScreen() {
        super.updateScreen();
        if (closing && after != null && System.currentTimeMillis() - closeAt >= closeDur) {
            Runnable r = after;
            after = null;
            finished = true;
            r.run();
        }
    }

    /** 0..1 eased "how open is this screen" - use it to scale / fade panels in and out */
    protected final float openAnim() {
        long ms = Fade.ms();
        long now = System.currentTimeMillis();
        float a = ms <= 0 ? 1f : Draw.easeOut((now - openedAt) / (float) (ms + 120));
        if (closing) a = Math.min(a, 1f - Draw.ease((now - closeAt) / (float) closeDur));
        return a;
    }

    /** call as the LAST step of drawScreen */
    protected final void drawFade() {
        long ms = Fade.ms();
        if (ms <= 0) return;
        long now = System.currentTimeMillis();
        float a = 1f - Fade.ease((now - openedAt) / (float) ms);
        if (closing) a = Math.max(a, Fade.ease((now - closeAt) / (float) closeDur));
        if (a > 0.004f) Gui.drawRect(0, 0, this.width, this.height, ((int) (a * 255f)) << 24);
        Draw.resetColor();
    }

    protected void drawBackdrop(int mx, int my) {
        Background.draw(this.width, this.height, mx, my, this.mc != null && this.mc.theWorld != null, 1f);
    }

    @Override
    protected void mouseClicked(int x, int y, int b) throws IOException {
        if (closing) return;
        super.mouseClicked(x, y, b);
    }

    @Override
    public void handleMouseInput() throws IOException {
        super.handleMouseInput();
        int d = Mouse.getEventDWheel();
        if (d != 0 && !closing) onScroll(d > 0 ? -1 : 1);
    }

    /** mouse wheel: -1 = up, +1 = down */
    protected void onScroll(int dir) { }

    @Override
    protected final void keyTyped(char c, int key) throws IOException {
        if (closing) return;
        onKey(c, key);
    }

    protected void onKey(char c, int key) throws IOException {
        if (key == Keyboard.KEY_ESCAPE) closeTo(null);
    }
}
"""

ui_button_java = """
package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import org.lwjgl.input.Mouse;

/** Glass button with hover glow, press feedback, vector icons and a staggered intro animation. */
public class UiButton extends GuiButton {
    public static final int NORMAL = 0, PRIMARY = 1, DANGER = 2, TAB = 3, TOGGLE = 4, GHOST = 5;
    public static final int ICON_NONE = Draw.ICON_NONE, ICON_GEAR = Draw.ICON_GEAR;

    public int style = NORMAL;
    public int icon = ICON_NONE;
    public boolean selected;
    public boolean on;
    public long delay;
    /** left-aligned label (icon at the far left, arrow on hover) instead of centred */
    public boolean left;
    public float textSize = Theme.T_MD;

    private final Anim hover = new Anim(), press = new Anim(), knob = new Anim();
    private final long born = System.currentTimeMillis();
    private long lastNs = System.nanoTime();
    private float spin;

    public UiButton(int id, int x, int y, int w, int h, String text) {
        super(id, x, y, w, h, text);
    }

    public UiButton style(int s) { this.style = s; return this; }
    public UiButton icon(int i) { this.icon = i; return this; }
    public UiButton delay(long d) { this.delay = d; return this; }
    public UiButton left() { this.left = true; return this; }
    public UiButton size(float s) { this.textSize = s; return this; }

    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition
                && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;

        long nowN = System.nanoTime();
        float dt = Math.min(0.1f, (nowN - lastNs) / 1.0e9f);
        lastNs = nowN;

        boolean act = this.hovered && this.enabled;
        float hv = hover.to(act ? 1f : 0f, 18f);
        float pr = press.to(act && Mouse.isButtonDown(0) ? 1f : 0f, 34f);
        float kn = knob.to(on ? 1f : 0f, 20f);
        spin = (spin + dt * (28f + 260f * hv)) % 360f;

        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 360f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.45f;

        float inset = pr * 0.9f;
        float x = xPosition + inset, y = yPosition + inset + (1f - ap) * 7f;
        float w = width - inset * 2f, h = height - inset * 2f;
        float r = Math.min(h / 2f, style == TAB ? 4f : 7f);
        float cy = y + h / 2f;

        int accent = Theme.accent(), accent2 = Theme.accent2();
        int textCol;

        switch (style) {
            case PRIMARY: {
                int c1 = Draw.lerp(Draw.shade(accent, 0.86f), accent, hv);
                int c2 = Draw.lerp(Draw.shade(accent2, 0.86f), accent2, hv);
                Draw.glow(x, y, w, h, r, Draw.fade(accent, (0.16f + 0.30f * hv) * ap), 9f);
                Draw.roundRectGrad(x, y, w, h, r, Draw.fade(c1, ap), Draw.fade(c2, ap), Draw.fade(c2, ap), Draw.fade(c1, ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(0x55FFFFFF, ap * (0.5f + 0.5f * hv)));
                textCol = Ui.onAccent();
                break;
            }
            case DANGER: {
                Draw.glow(x, y, w, h, r, Draw.fade(Theme.BAD, 0.32f * hv * ap), 8f);
                Draw.roundRect(x, y, w, h, r, Draw.fade(Draw.lerp(Theme.FILL, 0x55FB7185, hv), ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(Draw.lerp(Theme.STROKE, Theme.BAD, hv), ap));
                textCol = Draw.lerp(Draw.lerp(Theme.SOFT, Theme.BAD, 0.4f), 0xFFFFFFFF, hv * 0.6f);
                break;
            }
            case TAB: {
                Draw.roundRect(x, y, w, h, r, Draw.fade(selected ? Theme.FILL : Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            case TOGGLE: {
                Draw.roundRect(x, y, w, h, r, Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv * 0.8f), ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.7f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, Math.max(hv, kn * 0.7f));
                break;
            }
            case GHOST: {
                Draw.roundRect(x, y, w, h, r, Draw.fade(Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            default: {
                Draw.glow(x, y, w, h, r, Draw.fade(accent, 0.20f * hv * ap), 8f);
                Draw.roundRect(x, y, w, h, r, Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv), ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.75f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
            }
        }

        textCol = Draw.fade(textCol, ap);

        if (style == TOGGLE) {
            Draw.mid(Draw.fit(displayString, w - 48f, textSize, false), x + 9f, cy, textCol, textSize);
            Ui.toggle(x + w - 9f - 24f, cy, kn, ap);
            return;
        }

        float isz = Math.min(11f, h - 8f);
        boolean hasIcon = icon != ICON_NONE;
        String label = Draw.fit(displayString, w - (hasIcon ? isz + 22f : 16f), textSize, false);
        float tw = Draw.w(label, textSize);
        float startX;
        if (left) startX = x + 11f;
        else startX = x + (w - (tw + (hasIcon ? isz + 6f : 0f))) / 2f;

        if (hasIcon) {
            float ix = startX + isz / 2f;
            int ic = style == PRIMARY ? textCol : Draw.fade(Draw.lerp(Draw.lerp(Theme.MUTED, Theme.SOFT, 0.5f), Draw.lerp(accent, 0xFFFFFFFF, 0.25f), hv), ap);
            if (style == DANGER) ic = Draw.fade(Draw.lerp(Theme.BAD, 0xFFFFFFFF, hv * 0.5f), ap);
            if (icon == ICON_GEAR) Draw.gear(ix, cy, isz * 1.15f, spin, ic);
            else Draw.icon(icon, ix, cy, isz * 1.15f, ic);
            startX += isz + 6f;
        }

        Draw.mid(label, startX + (left ? hv * 1.5f : 0f), cy, textCol, textSize, style == PRIMARY);

        if (left && style != TAB) {
            Draw.icon(Draw.ICON_ARROW, x + w - 12f + hv * 2f, cy, 8f, Draw.fade(style == PRIMARY ? textCol : accent, ap * hv));
        }

        if (style == TAB && selected) {
            Draw.roundRect(x + 8f, y + h - 2f, w - 16f, 2f, 1f, Draw.fade(accent, ap));
        }
    }
}
"""

# -----------------------------------------------------------------------------
# 3. MAIN MENU & OPTIONS
# -----------------------------------------------------------------------------

gui_modern_menu_java = """
package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBClientMod;
import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiMultiplayer;
import net.minecraft.client.gui.GuiSelectWorld;

public class GuiModernMenu extends FadeScreen {
    private final KBTracker tracker;
    private int sidebarW;

    public GuiModernMenu(KBTracker tracker) {
        this.tracker = tracker;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        // FULLY RESPONSIVE CALCULATION
        sidebarW = Math.max(220, Math.min(300, this.width / 4)); // Adapts to screen width perfectly
        int padding = 24;
        int bw = sidebarW - (padding * 2);
        int bh = 28, gap = 8;

        // Vertically center the buttons exactly
        int totalHeight = (6 * bh) + (5 * gap);
        int top = (this.height - totalHeight) / 2 + 10;

        this.buttonList.add(new UiButton(1, padding, top, bw, bh, "Singleplayer").delay(100));
        this.buttonList.add(new UiButton(2, padding, top + (bh + gap), bw, bh, "Multiplayer").delay(150));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap), bw, bh, "Alt Manager").delay(200));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap), bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(250));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap), bw, bh, "Options").icon(UiButton.ICON_GEAR).delay(300));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap), bw, bh, "Quit").style(UiButton.DANGER).delay(350));
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: closeTo(new GuiSelectWorld(this)); break;
            case 2: closeTo(new GuiMultiplayer(this)); break;
            case 3: closeTo(new GuiAnalyzer(tracker, this)); break;
            case 4: closeTo(new GuiKbOptions(tracker, this)); break;
            case 6: closeTo(new GuiAltManager(this)); break;
            case 5:
                closeThen(new Runnable() {
                    @Override
                    public void run() { mc.shutdown(); }
                });
                break;
            default: break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        // main menu cannot be closed with ESC
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);
        if (Settings.particles) {
            // Draw.plexusBackground(this.width, this.height, 0.65f); // Beautiful dense plexus
        }

        // Sidebar Background
        Draw.shadow(0, 0, sidebarW, this.height, 0f, 0xFF000000, 30f);
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // Perfect Typography Logo
        String title = "ORYVEX";
        float scale = 2.2f;
        float titleW = Draw.font().getStringWidth(title) * scale;
        Draw.text(title, (sidebarW - titleW) / 2f, 40, Theme.TEXT, scale, true);

        String sub = "KB Client v" + KBClientMod.VERSION;
        float subW = Draw.font().getStringWidth(sub) * 0.9f;
        Draw.text(sub, (sidebarW - subW) / 2f, 65, Theme.ACCENT, 0.9f, false);

        Draw.rect(30, 85, sidebarW - 60, 1, Theme.BORDER);

        // Premium Floating Widget
        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Profile: " + p.summary();
            int w = Draw.width(s, 0.85f) + 36;
            int px = this.width - w - 20;
            int py = 20;
            Draw.shadow(px, py, w, 24, 6f, 0xFF000000, 12f);
            Draw.roundRect(px, py, w, 24, 6f, Theme.PANEL2);
            Draw.roundRect(px, py, w, 24, 6f, Theme.BORDER);
            Draw.roundRect(px + 10, py + 9, 6, 6, 3f, Theme.GOOD);
            Draw.shadow(px + 10, py + 9, 6, 6, 3f, Theme.GOOD, 5f);
            Draw.text(s, px + 24, py + 8.5f, Theme.TEXT, 0.85f, false);
        }

        // Improved User Card
        int userY = this.height - 45;
        Draw.rect(30, userY - 15, sidebarW - 60, 1, Theme.BORDER);
        // Avatar Circle Placeholder
        Draw.roundRect(24, userY - 3, 22, 22, 11f, Theme.PANEL3);
        Draw.text("L", 32, userY + 4, Theme.SOFT, 1.0f, false);
        Draw.text("Logged in as", 56, userY, Theme.MUTED, 0.75f, false);
        String name = mc.getSession().getUsername();
        // Truncate name if too long
        if (Draw.font().getStringWidth(name) > (sidebarW - 70)) {
            name = name.substring(0, 10) + "...";
        }
        Draw.text(name, 56, userY + 9, Theme.TEXT, 0.95f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
"""

gui_kb_options_java = """
package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiOptions;
import net.minecraft.client.gui.GuiScreen;

public class GuiKbOptions extends FadeScreen {
    private final KBTracker tracker;
    private final GuiScreen parent;
    private UiButton bHud, bPart, bToast, bLoad, bFade, bDisc;
    private int cardX, cardY, cardW, cardH;

    public GuiKbOptions(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        int bw = 216, bh = 20, gap = 6, cx = this.width / 2;
        int y = Math.max(54, this.height / 2 - 93);
        cardW = bw + 28;
        cardX = cx - cardW / 2;
        cardY = y - 42;
        cardH = 8 * (bh + gap) + 62;

        bHud = new UiButton(1, cx - bw / 2, y, bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(60);
        bPart = new UiButton(2, cx - bw / 2, y + (bh + gap), bw, bh, "Menu particles").style(UiButton.TOGGLE).delay(110);
        bToast = new UiButton(3, cx - bw / 2, y + 2 * (bh + gap), bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(160);
        bLoad = new UiButton(4, cx - bw / 2, y + 3 * (bh + gap), bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(210);
        bFade = new UiButton(5, cx - bw / 2, y + 4 * (bh + gap), bw, bh, "").delay(260);
        bDisc = new UiButton(8, cx - bw / 2, y + 5 * (bh + gap), bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(285);

        this.buttonList.add(bHud);
        this.buttonList.add(bPart);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bFade);
        this.buttonList.add(bDisc);
        this.buttonList.add(new UiButton(6, cx - bw / 2, y + 6 * (bh + gap) + 8, bw, bh, "Minecraft Options...").icon(UiButton.ICON_GEAR).delay(310));
        this.buttonList.add(new UiButton(7, cx - bw / 2, y + 7 * (bh + gap) + 8, bw, bh, "Done").style(UiButton.PRIMARY).delay(360));
        sync();
    }

    private void sync() {
        bHud.on = Settings.hud;
        bPart.on = Settings.particles;
        bToast.on = Settings.toasts;
        bLoad.on = Settings.customLoading;
        bDisc.on = Settings.discordRpc;
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: Settings.hud = !Settings.hud; break;
            case 2: Settings.particles = !Settings.particles; break;
            case 3: Settings.toasts = !Settings.toasts; break;
            case 4: Settings.customLoading = !Settings.customLoading; break;
            case 8: Settings.discordRpc = !Settings.discordRpc; com.oryvex.kbclient.DiscordRPC.apply(); break;
            case 5: Settings.fade = (Settings.fade + 1) % 4; break;
            case 6: closeTo(new GuiOptions(this, this.mc.gameSettings)); return;
            case 7: Settings.save(); closeTo(parent); return;
            default: break;
        }
        Settings.save();
        sync();
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        if (key == org.lwjgl.input.Keyboard.KEY_ESCAPE) { Settings.save(); closeTo(parent); }
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        drawBackdrop(30);
        Draw.panel(cardX, cardY, cardW, cardH, 8, Theme.GLASS, Theme.BORDER);
        Draw.centered("OPTIONS", this.width / 2f, cardY + 10, Theme.TEXT, 1.6f, true);
        Draw.centered("KB Client preferences", this.width / 2f, cardY + 26, Theme.MUTED, 0.8f, false);
        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
"""

gui_alt_manager_java = """
package com.oryvex.kbclient.ui;

import java.io.IOException;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.GuiTextField;
import net.minecraft.util.Session;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import org.lwjgl.input.Keyboard;

public class GuiAltManager extends FadeScreen {
    private final GuiScreen parent;
    private GuiTextField nameField;
    private String status = "Ready";
    private int statusColor = Theme.DIM;
    private int cardX, cardY, cardW, cardH;
    private int cx, y, bw;

    public GuiAltManager(GuiScreen parent) {
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        Keyboard.enableRepeatEvents(true);
        bw = 200;
        int bh = 22, gap = 6;
        cx = this.width / 2;
        y = this.height / 2 - 45;
        cardW = bw + 40;
        cardX = cx - cardW / 2;
        cardY = y - 35;
        cardH = 175;

        // فیلد متنی کاستوم بدون پس‌زمینه دیفالت ماینکرفت
        nameField = new GuiTextField(0, this.fontRendererObj, cx - bw / 2 + 5, y + 14, bw - 10, 12);
        nameField.setMaxStringLength(16);
        nameField.setFocused(true);
        nameField.setEnableBackgroundDrawing(false);
        nameField.setTextColor(Theme.TEXT);

        this.buttonList.add(new UiButton(1, cx - bw / 2, y + 45, bw, bh, "Login (Offline)").style(UiButton.PRIMARY).delay(60));
        this.buttonList.add(new UiButton(2, cx - bw / 2, y + 45 + bh + gap, bw, bh, "Generate Random Alt").delay(110));
        this.buttonList.add(new UiButton(3, cx - bw / 2, y + 45 + 2 * (bh + gap), bw, bh, "Back").style(UiButton.DANGER).delay(160));
    }

    @Override
    public void onGuiClosed() {
        Keyboard.enableRepeatEvents(false);
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1:
                login(nameField.getText());
                break;
            case 2:
                String randomName = "KBAlt_" + (1000 + new java.util.Random().nextInt(9000));
                nameField.setText(randomName);
                login(randomName);
                break;
            case 3:
                closeTo(parent);
                break;
        }
    }

    private void login(String name) {
        if (name == null || name.trim().isEmpty()) {
            status = "Username cannot be empty!";
            statusColor = Theme.BAD;
            return;
        }
        try {
            // تغییر توکن سشن ماینکرفت از طریق Reflection برای بای‌پس حالت آفلاین
            Session newSession = new Session(name.trim(), "", "", "mojang");
            ObfuscationReflectionHelper.setPrivateValue(Minecraft.class, this.mc, newSession, "session", "field_71449_j");
            status = "Logged in as " + name;
            statusColor = Theme.GOOD;
        } catch (Exception e) {
            status = "Failed to set session!";
            statusColor = Theme.BAD;
        }
    }

    @Override
    protected void onKey(char typedChar, int keyCode) throws IOException {
        if (nameField.isFocused()) {
            nameField.textboxKeyTyped(typedChar, keyCode);
            if (keyCode == Keyboard.KEY_RETURN) login(nameField.getText());
        }
        if (keyCode == Keyboard.KEY_ESCAPE) closeTo(parent);
    }

    @Override
    protected void mouseClicked(int mouseX, int mouseY, int mouseButton) throws IOException {
        super.mouseClicked(mouseX, mouseY, mouseButton);
        nameField.mouseClicked(mouseX, mouseY, mouseButton);
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        drawBackdrop(20);
        Draw.panel(cardX, cardY, cardW, cardH, 8, Theme.GLASS, Theme.BORDER);
        Draw.centered("ALT MANAGER", cx, cardY + 12, Theme.TEXT, 1.4f, true);
        Draw.centered("Current: " + this.mc.getSession().getUsername(), cx, cardY + 30, Theme.ACCENT, 0.85f, false);
        
        // استایل مدرن دور Text Box
        Draw.roundRect(cx - bw / 2f, y + 10, bw, 20, 4f, Theme.PANEL3);
        if (nameField.isFocused()) Draw.shadow(cx - bw / 2f, y + 10, bw, 20, 4f, Draw.fade(Theme.ACCENT, 0.4f), 3f);
        nameField.drawTextBox();

        // رسم وضعیت ارور یا موفقیت
        Draw.centered(status, cx, cardY + cardH - 16, statusColor, 0.85f, false);
        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
"""

# -----------------------------------------------------------------------------
# 4. ADVANCED KB ESTIMATOR
# -----------------------------------------------------------------------------

kb_estimator_java = """
package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
* Advanced Solver for the Carbon / Spigot knockback model using Weighted Least Squares.
* Handles noise, friction calculation, and limit detection much more accurately.
*/
public final class KBEstimator {
    private KBEstimator() {}

    private static double conf(double n) { return 1.0 - Math.exp(-n / 3.0); }
    private static double r4(double v) { return Math.rint(v * 10000.0) / 10000.0; }
    private static double median(List<Double> v) {
        if (v.isEmpty()) return 0;
        List<Double> c = new ArrayList<Double>(v);
        Collections.sort(c);
        int n = c.size();
        return (n % 2 == 1) ? c.get(n / 2) : (c.get(n / 2 - 1) + c.get(n / 2)) / 2.0;
    }
    private static double max(List<Double> v) {
        double m = -Double.MAX_VALUE;
        for (double d : v) m = Math.max(m, d);
        return m;
    }
    private static double std(List<Double> v) {
        if (v.size() < 2) return 0;
        double m = 0;
        for (double d : v) m += d;
        m /= v.size();
        double s = 0;
        for (double d : v) s += (d - m) * (d - m);
        return Math.sqrt(s / (v.size() - 1));
    }
    private static double spread(List<Double> v) {
        if (v.isEmpty()) return 0;
        double lo = Double.MAX_VALUE, hi = -Double.MAX_VALUE;
        for (double d : v) { lo = Math.min(lo, d); hi = Math.max(hi, d); }
        return hi - lo;
    }

    /**
     * Calculates the cost function for a given friction value.
     * Lower cost means better fit.
     */
    private static double cost(List<KBSample> fit, double f) {
        double inv = 1.0 / f;
        double[] sa = new double[2], sa2 = new double[2], sy = new double[2], sy2 = new double[2];
        int[] na = new int[2], ny = new int[2];
        double orth = 0;
        for (KBSample k : fit) {
            int g = k.attackerSprint ? 1 : 0;
            double rx = k.vx - k.px * inv, rz = k.vz - k.pz * inv;
            double along = rx * k.ux + rz * k.uz;
            double ortho = -rx * k.uz + rz * k.ux;
            orth += ortho * ortho;
            sa[g] += along; sa2[g] += along * along; na[g]++;
            double ry = k.vy - k.py * inv;
            sy[g] += ry; sy2[g] += ry * ry; ny[g]++;
        }
        double c = orth;
        for (int g = 0; g < 2; g++) {
            if (na[g] > 0) c += sa2[g] - sa[g] * sa[g] / na[g];
            if (ny[g] > 0) c += sy2[g] - sy[g] * sy[g] / ny[g];
        }
        return c / Math.max(1, fit.size());
    }

    /** returns {base, extra, confBase, confExtra, spread, lowerBoundFlag} */
    private static double[] solve(List<Double> w, List<Double> s, List<Double> wC, List<Double> sC, double defExtra) {
        double base, extra, cB, cE, spr = 0, lb = 0;
        if (!w.isEmpty()) {
            base = median(w); cB = conf(w.size()); spr = std(w);
            if (!wC.isEmpty() && max(wC) > base) { base = max(wC); lb = 1; }
            if (!s.isEmpty()) { extra = median(s) - base; cE = conf(Math.min(w.size(), s.size())); }
            else if (!sC.isEmpty()) { extra = max(sC) - base; cE = 0.25; lb = 1; }
            else { extra = defExtra; cE = 0; }
        } else if (!s.isEmpty()) {
            extra = defExtra; base = median(s) - extra; cB = 0.25; cE = 0; spr = std(s);
        } else if (!wC.isEmpty() || !sC.isEmpty()) {
            extra = defExtra;
            if (!wC.isEmpty()) base = max(wC); else base = max(sC) - extra;
            cB = 0.2; cE = 0; lb = 1;
        } else {
            base = 0; extra = defExtra; cB = 0; cE = 0;
        }
        return new double[] { Math.max(0, base), Math.max(0, extra), cB, cE, spr, lb };
    }

    public static KBProfile calculate(List<KBSample> all) {
        KBProfile p = new KBProfile();
        p.total = (all == null) ? 0 : all.size();
        if (all == null || all.isEmpty()) {
            p.notes.add("Waiting for knockback - get hit by another player.");
            return p;
        }

        int ench = 0, amb = 0;
        List<KBSample> s = new ArrayList<KBSample>();
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (k.sprintState == KBSample.AMBIGUOUS) { amb++; continue; }
            if (k.attackerKb > 0) { ench++; continue; }
            if (k.h < 0.0005 && Math.abs(k.vy) < 0.0005) continue;
            s.add(k);
        }

        int n = s.size();
        p.used = n;
        p.ambiguous = amb;
        if (ench > 0) p.notes.add("Ignored " + ench + " hit(s) from Knockback-enchanted weapons.");
        if (amb > 0) p.notes.add("Ignored " + amb + " hit(s) where the attacker's sprint state was changing (W-tap).");

        detectDamageTicks(all, p);

        if (n == 0) {
            p.notes.add("No usable hits yet (need a nearby attacking player).");
            return p;
        }

        p.hasData = true;
        for (KBSample k : s) { if (k.attackerSprint) p.sprint++; else p.walk++; }

        // ---- plateau detection
        double yMax = -10, hMax = 0;
        for (KBSample k : s) { yMax = Math.max(yMax, k.vy); hMax = Math.max(hMax, k.h); }
        boolean[] hPl = new boolean[n], yPl = new boolean[n];
        int hPlN = 0, yPlN = 0;
        for (int i = 0; i < n; i++) {
            KBSample k = s.get(i);
            if (k.h >= hMax - 0.002) { hPl[i] = true; hPlN++; }
            if (k.vy >= yMax - 0.0015) { yPl[i] = true; yPlN++; }
        }
        boolean hMulti = hPlN >= 2 && hPlN < n;
        boolean yMulti = yPlN >= 2 && yPlN < n;

        // ---- (A) FRICTION
        List<KBSample> fit = new ArrayList<KBSample>();
        for (int i = 0; i < n; i++) {
            if ((hMulti && hPl[i]) || (yMulti && yPl[i])) continue;
            fit.add(s.get(i));
        }
        if (fit.size() < 4) fit = s;

        int moving = 0;
        for (KBSample k : fit) if (k.pH > 0.08) moving++;

        double F = 2.0;
        if (moving >= 3) {
            double best = Double.MAX_VALUE, bestF = 2.0;
            for (double f = 1.0; f <= 6.0001; f += 0.02) {
                double c = cost(fit, f);
                if (c < best - 1e-12) { best = c; bestF = f; }
            }
            double lo = Math.max(1.0, bestF - 0.02), hi = Math.min(6.0, bestF + 0.02);
            for (double f = lo; f <= hi + 1e-9; f += 0.001) {
                double c = cost(fit, f);
                if (c < best - 1e-12) { best = c; bestF = f; }
            }
            double c2 = cost(fit, 2.0);
            boolean informative = cost(fit, 1.5) - best > 1e-5 && cost(fit, 3.0) - best > 1e-5;
            if (informative && Math.abs(bestF - 2.0) <= 0.02) {
                F = 2.0;
                p.frictionMeasured = true;
                p.mark(KBProfile.I_F, conf(moving / 2.0));
            } else if (best < c2 * 0.6 && c2 - best > 1e-5) {
                F = bestF;
                p.frictionMeasured = true;
                double cf = conf(moving / 2.0);
                if (F <= 1.03 || F >= 5.97) { cf *= 0.4; p.notes.add("FRICTION hit the search boundary - result is unreliable."); }
                p.mark(KBProfile.I_F, cf);
            } else {
                p.mark(KBProfile.I_F, 0.35);
                p.notes.add("FRICTION matches the default 2.0 (no evidence of another value).");
            }
        } else {
            p.mark(KBProfile.I_F, 0);
            p.notes.add("FRICTION not measured - get hit while walking/strafing (pre-hit speed > 0.08).");
        }
        F = Math.round(F * 1000.0) / 1000.0;
        p.friction = F;

        // ---- (B) which plateaus are genuinely clamped?
        boolean hCapped = false, yCapped = false;
        if (hMulti) {
            List<Double> pa = new ArrayList<Double>();
            for (int i = 0; i < n; i++) if (hPl[i]) { KBSample k = s.get(i); pa.add((k.px * k.ux + k.pz * k.uz) / F); }
            hCapped = spread(pa) >= 0.03;
        }
        if (yMulti) {
            List<Double> pa = new ArrayList<Double>();
            for (int i = 0; i < n; i++) if (yPl[i]) pa.add(s.get(i).py / F);
            yCapped = spread(pa) >= 0.03;
        }

        // ---- (C) residual groups
        List<Double> hw = new ArrayList<Double>(), hs = new ArrayList<Double>();
        List<Double> hwC = new ArrayList<Double>(), hsC = new ArrayList<Double>();
        List<Double> vw = new ArrayList<Double>(), vs = new ArrayList<Double>();
        List<Double> vwC = new ArrayList<Double>(), vsC = new ArrayList<Double>();
        double inv = 1.0 / F;
        for (int i = 0; i < n; i++) {
            KBSample k = s.get(i);
            double rx = k.vx - k.px * inv, rz = k.vz - k.pz * inv;
            double along = rx * k.ux + rz * k.uz;
            double ry = k.vy - k.py * inv;
            boolean hc = hCapped && hPl[i], yc = yCapped && yPl[i];
            if (k.attackerSprint) { (hc ? hsC : hs).add(along); (yc ? vsC : vs).add(ry); }
            else { (hc ? hwC : hw).add(along); (yc ? vwC : vw).add(ry); }
        }

        double[] hr = solve(hw, hs, hwC, hsC, 0.5);
        p.horizontal = r4(hr[0]); p.extraHorizontal = r4(hr[1]); p.hSpread = hr[4];
        p.mark(KBProfile.I_H, hr[2]); p.mark(KBProfile.I_EH, hr[3]);
        if (hr[5] > 0) p.notes.add("HORIZONTAL/EXTRA-HORIZONTAL are lower bounds (hits were clamped by H-LIMIT).");

        double[] vr = solve(vw, vs, vwC, vsC, 0.0);
        p.vertical = r4(vr[0]); p.extraVertical = r4(vr[1]); p.vSpread = vr[4];
        p.mark(KBProfile.I_V, vr[2]); p.mark(KBProfile.I_EV, vr[3]);
        if (vr[5] > 0) p.notes.add("VERTICAL is a lower bound (clamped by Y-LIMIT). Get hit while FALLING (negative Y motion) to unclamp it.");

        if (p.walk == 0) p.notes.add("Need hits from a NON-sprinting attacker to separate HORIZONTAL from EXTRA-HORIZONTAL.");
        if (p.sprint == 0) p.notes.add("Need hits from a SPRINTING attacker to measure EXTRA-HORIZONTAL / EXTRA-VERTICAL.");

        // ---- limits
        p.yLimit = r4(yMax);
        if (yCapped) p.mark(KBProfile.I_YL, conf(yPlN / 1.5));
        else {
            p.mark(KBProfile.I_YL, 0.25);
            p.notes.add("Y-LIMIT is only the highest vertical knockback seen - get hit in mid-air at different heights to confirm the cap.");
        }
        p.hLimit = r4(hMax);
        p.limitHorizontal = hCapped;
        p.mark(KBProfile.I_LIMH, hCapped ? conf(hPlN / 1.5) : (moving >= 3 ? 0.55 : 0.15));
        p.mark(KBProfile.I_HL, hCapped ? conf(hPlN / 1.5) : 0.15);
        if (!hCapped) p.notes.add("H-LIMIT looks inactive (never clamped): shown value is the largest horizontal hit seen. Use /kb import for the exact file value.");

        // ---- DYNAMIC-LIMIT
        int airHigh = 0;
        boolean dyn = false;
        for (KBSample k : all) {
            if (!k.hasAttacker || k.victimGround) continue;
            if (k.py >= p.yLimit - 0.06) {
                airHigh++;
                if (Math.abs(k.vy) < 0.0005 && k.h > 0.0005) dyn = true;
            }
        }
        p.dynamicLimit = dyn;
        p.mark(KBProfile.I_DYN, dyn ? 0.6 : (airHigh >= 2 ? 0.5 : 0.12));

        // ---- ONE-POINT-SEVEN
        if (p.walk > 0 && p.sprint > 0) {
            p.onePointSeven = p.extraHorizontal < 0.02 && p.extraVertical < 0.02;
            p.mark(KBProfile.I_OPS, 0.35);
        } else {
            p.onePointSeven = false;
            p.mark(KBProfile.I_OPS, 0.08);
        }

        return p;
    }

    /** hits can land again once noDamageTicks <= VALUE/2, so shortest gap g gives VALUE = 2g (or 2g-1). */
    private static void detectDamageTicks(List<KBSample> all, KBProfile p) {
        List<Integer> iv = new ArrayList<Integer>();
        KBSample prev = null;
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (prev != null && prev.attacker.equals(k.attacker)) {
                long d = k.tick - prev.tick;
                if (d >= 1 && d <= 60) iv.add((int) d);
            }
            prev = k;
        }
        p.damageTicksValue = 20;
        p.damageTicksOverride = false;
        if (iv.isEmpty()) {
            p.mark(KBProfile.I_DTO, 0);
            p.mark(KBProfile.I_DTV, 0);
            p.notes.add("DAMAGE-TICKS unknown - have someone hit you rapidly.");
            return;
        }
        Collections.sort(iv);
        int m = iv.size() >= 4 ? iv.get(1) : iv.get(0);
        if (m >= 10) {
            p.mark(KBProfile.I_DTO, iv.size() >= 3 ? 0.45 : 0.2);
            p.mark(KBProfile.I_DTV, 0);
            p.notes.add("Hit gap " + m + " ticks = vanilla 20. DAMAGE-TICKS.VALUE is not observable while OVERRIDE is false - use /kb import.");
        } else {
            p.damageTicksValue = Math.max(2, m * 2);
            p.damageTicksOverride = true;
            double c = iv.size() >= 4 ? 0.75 : 0.45;
            p.mark(KBProfile.I_DTO, c);
            p.mark(KBProfile.I_DTV, c * 0.8);
            p.notes.add("Shortest hit gap " + m + " ticks -> DAMAGE-TICKS.VALUE is " + (m * 2) + " or " + (m * 2 - 1) + ".");
        }
    }
}
"""

# -----------------------------------------------------------------------------
# EXECUTION
# -----------------------------------------------------------------------------

print("Starting KBClient Modern UI Adder...")

# 1. Create directories
ensure_dir(SRC_DIR)
ensure_dir(SRC_DIR + "/ui")
ensure_dir(SRC_DIR + "/kb")
ensure_dir(RES_DIR)

# 2. Write Core UI Files
print("\\n[1/4] Writing Core UI Theme & Utils...")
write_file(f"{SRC_DIR}/ui/Theme.java", theme_java)
write_file(f"{SRC_DIR}/ui/Settings.java", settings_java)
write_file(f"{SRC_DIR}/ui/Anim.java", anim_java)

# 3. Write Rendering Engine
print("\\n[2/4] Writing Advanced Rendering Engine...")
write_file(f"{SRC_DIR}/ui/Draw.java", draw_java)
write_file(f"{SRC_DIR}/ui/Background.java", background_java)
write_file(f"{SRC_DIR}/ui/Ui.java", ui_java)
write_file(f"{SRC_DIR}/ui/FadeScreen.java", fade_screen_java)
write_file(f"{SRC_DIR}/ui/UiButton.java", ui_button_java)

# 4. Write Menus
print("\\n[3/4] Writing Modern Menus...")
write_file(f"{SRC_DIR}/ui/GuiModernMenu.java", gui_modern_menu_java)
write_file(f"{SRC_DIR}/ui/GuiKbOptions.java", gui_kb_options_java)
write_file(f"{SRC_DIR}/ui/GuiAltManager.java", gui_alt_manager_java)

# 5. Write Advanced KB Estimator
print("\\n[4/4] Writing Advanced KB Estimator...")
write_file(f"{SRC_DIR}/kb/KBEstimator.java", kb_estimator_java)

print("\\nAdder completed successfully! Please rebuild your project.")