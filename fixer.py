#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fixer.py — KB Client: تعمیر کامل GUI / فونت / رنگ / ریسپانسیو
از ریشه پروژه (پوشه‌ای که src/ دارد) اجرا کن.
"""
import sys
from pathlib import Path


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "src" / "main" / "java").is_dir():
            return p
    if (Path.cwd() / "src" / "main" / "java").is_dir():
        return Path.cwd()
    sys.exit("Project root (src/main/java) not found.")


ROOT = find_root()
JAVA = ROOT / "src" / "main" / "java" / "com" / "oryvex" / "kbclient"
UI   = JAVA / "ui"
FONT = JAVA / "font"
RES  = ROOT / "src" / "main" / "resources"

for d in (UI, FONT, RES / "fonts"):
    d.mkdir(parents=True, exist_ok=True)


def write(path: Path, body: str):
    path.write_text(body, encoding="utf-8")
    print(f"  [WRITE] {path.relative_to(ROOT)}")


# ===========================================================================
# 1) Theme.java — مقیاس‌ها ضریب باشند نه پیکسل
# ===========================================================================
write(UI / "Theme.java", r'''package com.oryvex.kbclient.ui;

public final class Theme {
    private Theme() {}

    // ---- surfaces ----
    public static final int BG0 = 0xFF05060B;
    public static final int BG1 = 0xFF0B0D16;
    public static final int PANEL = 0xFF121A29;
    public static final int PANEL2 = 0xFF182235;
    public static final int PANEL3 = 0xFF22304A;
    public static final int BORDER = 0xFF25324B;
    public static final int BORDER_HI = 0xFF3B5078;
    public static final int GLASS = 0xA6090B12;
    public static final int FILL = 0x16FFFFFF;
    public static final int FILL_HI = 0x2AFFFFFF;
    public static final int STROKE = 0x1FFFFFFF;
    public static final int STROKE_HI = 0x47FFFFFF;
    public static final int SURFACE2 = 0xFF141722;
    public static final int SURFACE3 = 0xFF1C2030;

    // ---- status ----
    public static final int GOOD = 0xFF34D399;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD = 0xFFFB7185;

    // ---- text ----
    public static final int TEXT = 0xFFF4F6FB;
    public static final int SOFT = 0xFFB4BCCF;
    public static final int MUTED = 0xFF7C86A2;
    public static final int DIM = 0xFF4A5169;

    // ---- type scale (ضریب روی فونت 9px) ----
    public static final float T_XS = 0.75f;
    public static final float T_SM = 0.85f;
    public static final float T_MD = 1.00f;
    public static final float T_LG = 1.25f;
    public static final float T_XL = 1.60f;

    public static final String S = "\u00a7";

    // ---- accent themes ----
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

    public static int flow(float offset) {
        float p = ((System.currentTimeMillis() % 7000L) / 7000f + offset) % 1f;
        if (p < 0f) p += 1f;
        float tri = p < 0.5f ? p * 2f : (1f - p) * 2f;
        return Draw.lerp(accent(), accent2(), tri);
    }

    public static float phase() { return (System.currentTimeMillis() % 7000L) / 7000f; }

    // aliases برای سازگاری با کد قدیمی
    public static final int ACCENT = 0xFF22D3EE;
    public static final int ACCENT_DK = 0xFF0E7490;
    public static final int ACCENT2 = 0xFFA78BFA;
}
''')


# ===========================================================================
# 2) ModernFontRenderer.java — TextLayout برای شکل‌گیری صحیح فارسی
# ===========================================================================
write(FONT / "ModernFontRenderer.java", r'''package com.oryvex.kbclient.font;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.font.FontRenderContext;
import java.awt.font.TextLayout;
import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.Tessellator;
import net.minecraft.client.renderer.WorldRenderer;
import net.minecraft.client.renderer.texture.TextureManager;
import net.minecraft.client.renderer.texture.TextureUtil;
import net.minecraft.client.renderer.vertex.DefaultVertexFormats;
import net.minecraft.client.settings.GameSettings;
import net.minecraft.util.ResourceLocation;

/**
 * AWT-backed font renderer with proper Arabic/Persian shaping via TextLayout.
 * Width measurement and drawing use the same cached texture, so layout never drifts.
 */
public class ModernFontRenderer extends FontRenderer {

    private static final int FONT_SIZE  = 32;
    private static final int BASE_HEIGHT = 9;

    private static final int[] COLOR_CODES = new int[32];
    static {
        for (int i = 0; i < 32; ++i) {
            int j = (i >> 3 & 1) * 85;
            int k = (i >> 2 & 1) * 170 + j;
            int l = (i >> 1 & 1) * 170 + j;
            int i1 = (i >> 0 & 1) * 170 + j;
            if (i == 6) k += 85;
            if (i >= 16) { k /= 4; l /= 4; i1 /= 4; }
            COLOR_CODES[i] = (k & 255) << 16 | (l & 255) << 8 | i1 & 255;
        }
    }

    private final Font inter;
    private final Font vazir;
    private final FontRenderContext frc = new FontRenderContext(null, true, true);

    private static final class GlyphTex {
        final int id, width, height;
        final float scale;
        GlyphTex(int id, int w, int h, float s) {
            this.id = id; this.width = w; this.height = h; this.scale = s;
        }
    }

    private final Map<String, GlyphTex> cache = new LinkedHashMap<String, GlyphTex>(512, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, GlyphTex> eldest) {
            if (size() > 512) {
                try { GlStateManager.deleteTexture(eldest.getValue().id); } catch (Throwable ignored) {}
                return true;
            }
            return false;
        }
    };

    public ModernFontRenderer(GameSettings gs, ResourceLocation loc, TextureManager tm, boolean unicode) {
        super(gs, loc, tm, unicode);
        Font i = load("/fonts/Inter-Regular.ttf");
        Font v = load("/fonts/Vazirmatn-Regular.ttf");
        this.inter = (i != null) ? i : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.vazir = (v != null) ? v : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.FONT_HEIGHT = BASE_HEIGHT;
    }

    private Font load(String path) {
        try {
            InputStream is = ModernFontRenderer.class.getResourceAsStream(path);
            if (is == null) return null;
            Font f = Font.createFont(Font.TRUETYPE_FONT, is).deriveFont((float) FONT_SIZE);
            is.close();
            return f;
        } catch (Throwable t) { return null; }
    }

    public static boolean hasRtl(String text) {
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if ((c >= 0x0590 && c <= 0x05FF)
             || (c >= 0x0600 && c <= 0x06FF)
             || (c >= 0x0750 && c <= 0x077F)
             || (c >= 0x08A0 && c <= 0x08FF)
             || (c >= 0xFB1D && c <= 0xFDFF)
             || (c >= 0xFE70 && c <= 0xFEFF)) return true;
        }
        return false;
    }

    private GlyphTex bake(String text) {
        Font font = hasRtl(text) ? vazir : inter;

        TextLayout layout = new TextLayout(text, font, frc);
        Rectangle2D b = layout.getBounds();
        int pad = 2;
        int w = Math.max(1, (int) Math.ceil(b.getWidth())  + pad * 2);
        int h = Math.max(1, (int) Math.ceil(b.getHeight()) + pad * 2);
        int baseline = (int) Math.ceil(layout.getAscent()) + pad;

        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,        RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,   RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS,   RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setColor(Color.WHITE);
        layout.draw(g, pad, baseline);
        g.dispose();

        int id = TextureUtil.glGenTextures();
        TextureUtil.uploadTextureImageAllocate(id, img, true, false);

        float scale = (float) BASE_HEIGHT / FONT_SIZE;
        return new GlyphTex(id, w, h, scale);
    }

    @Override
    public int drawString(String text, float x, float y, int color, boolean dropShadow) {
        if (text == null || text.isEmpty()) return (int) x;
        if (dropShadow) draw(text, x + 1f, y + 1f, color, true);
        return draw(text, x, y, color, false);
    }

    @Override
    public int drawStringWithShadow(String text, float x, float y, int color) {
        return drawString(text, x, y, color, true);
    }

    private int draw(String text, float x, float y, int color, boolean shadow) {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.enableTexture2D();

        float curX = x;
        int curColor = color;
        if ((curColor & 0xFC000000) == 0) curColor |= 0xFF000000;
        if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000);

        int i = 0;
        final int n = text.length();
        while (i < n) {
            if (text.charAt(i) == '\u00a7' && i + 1 < n) {
                char code = Character.toLowerCase(text.charAt(i + 1));
                int ci = "0123456789abcdef".indexOf(code);
                if (ci >= 0) {
                    curColor = COLOR_CODES[ci];
                    if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000);
                    else curColor |= 0xFF000000;
                } else if (code == 'r') {
                    curColor = color;
                    if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000);
                }
                i += 2;
                continue;
            }
            int j = i;
            while (j < n && text.charAt(j) != '\u00a7') j++;
            String piece = text.substring(i, j);
            i = j;
            if (piece.isEmpty()) continue;

            GlyphTex tex = cache.get(piece);
            if (tex == null) { tex = bake(piece); cache.put(piece, tex); }

            GlStateManager.bindTexture(tex.id);
            float r = (curColor >> 16 & 255) / 255f;
            float g = (curColor >> 8  & 255) / 255f;
            float b = (curColor       & 255) / 255f;
            float a = (curColor >>> 24      ) / 255f;
            GlStateManager.color(r, g, b, a);

            float s = tex.scale;
            GlStateManager.pushMatrix();
            GlStateManager.scale(s, s, 1f);

            float dx = curX / s;
            float dy = y / s;
            float dw = tex.width;
            float dh = tex.height;

            Tessellator t = Tessellator.getInstance();
            WorldRenderer wr = t.getWorldRenderer();
            wr.begin(7, DefaultVertexFormats.POSITION_TEX);
            wr.pos(dx,      dy + dh, 0.0D).tex(0.0D, 1.0D).endVertex();
            wr.pos(dx + dw, dy + dh, 0.0D).tex(1.0D, 1.0D).endVertex();
            wr.pos(dx + dw, dy,      0.0D).tex(1.0D, 0.0D).endVertex();
            wr.pos(dx,      dy,      0.0D).tex(0.0D, 0.0D).endVertex();
            t.draw();

            GlStateManager.popMatrix();
            curX += tex.width * s;
        }

        GlStateManager.color(1f, 1f, 1f, 1f);
        return (int) curX;
    }

    @Override
    public int getStringWidth(String text) {
        if (text == null || text.isEmpty()) return 0;
        float w = 0;
        int i = 0;
        final int n = text.length();
        while (i < n) {
            if (text.charAt(i) == '\u00a7' && i + 1 < n) { i += 2; continue; }
            int j = i;
            while (j < n && text.charAt(j) != '\u00a7') j++;
            String piece = text.substring(i, j);
            i = j;
            if (piece.isEmpty()) continue;
            GlyphTex tex = cache.get(piece);
            if (tex == null) { tex = bake(piece); cache.put(piece, tex); }
            w += tex.width * tex.scale;
        }
        return (int) Math.ceil(w);
    }

    @Override
    public int getCharWidth(char c) {
        if (c == '\u00a7') return -1;
        return getStringWidth(String.valueOf(c));
    }

    @Override
    public boolean getUnicodeFlag() { return false; }

    @Override
    public void onResourceManagerReload(net.minecraft.client.resources.IResourceManager rm) {
        // keep our fonts across reloads
    }
}
''')


# ===========================================================================
# 3) Settings.java
# ===========================================================================
write(UI / "Settings.java", r'''package com.oryvex.kbclient.ui;

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
    public static int density = 60;

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
''')


# ===========================================================================
# 4) Draw.java — ساده‌سازی رسم متن: baseline واقعی فونت رعایت شود
#    (قبلاً mid() از 4f*scale استفاده می‌کرد که با فونت فارسی درست نبود)
# ===========================================================================
write(UI / "Draw.java", r'''package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import org.lwjgl.opengl.GL11;

import java.util.ArrayList;
import java.util.List;

public final class Draw {
    private Draw() {}

    public static final int ICON_NONE = 0, ICON_GEAR = 1, ICON_ARROW = 2;

    // ---- math ----
    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }
    public static float ease(float t) { t = clamp(t); return t * t * (3f - 2f * t); }
    public static float easeOut(float t) { t = clamp(t); return 1f - (1f - t) * (1f - t); }
    public static float lerp(float a, float b, float t) { return a + (b - a) * clamp(t); }

    public static int lerp(int a, int b, float t) {
        t = clamp(t);
        int aa = (a >>> 24) & 255, ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
        int ba = (b >>> 24) & 255, br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;
        return (((int)(aa + (ba - aa) * t)) << 24)
             | (((int)(ar + (br - ar) * t)) << 16)
             | (((int)(ag + (bg - ag) * t)) << 8)
             |  ((int)(ab + (bb - ab) * t));
    }

    public static int alpha(int color, float a) {
        return ((int)(clamp(a) * 255f) << 24) | (color & 0xFFFFFF);
    }

    public static int fade(int color, float a) {
        return ((int)(((color >>> 24) & 255) * clamp(a)) << 24) | (color & 0xFFFFFF);
    }

    public static int shade(int color, float s) {
        float r = ((color >> 16) & 255) / 255f;
        float g = ((color >> 8)  & 255) / 255f;
        float b = ( color        & 255) / 255f;
        r *= s; g *= s; b *= s;
        return (color & 0xFF000000)
             | (((int)(r * 255)) << 16)
             | (((int)(g * 255)) << 8)
             |  ((int)(b * 255));
    }

    public static int confColor(double c) {
        float f = (float) Math.max(0, Math.min(1, c));
        return f < 0.5f ? lerp(Theme.BAD, Theme.WARN, f * 2f)
                        : lerp(Theme.WARN, Theme.GOOD, (f - 0.5f) * 2f);
    }

    // ---- GL state ----
    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void resetColor() {
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.disableBlend();
    }

    // ---- primitives ----
    public static void rect(float x, float y, float w, float h, int color) {
        Gui.drawRect((int)x, (int)y, (int)(x + w), (int)(y + h), color);
    }

    public static void vgradient(int w, int h, int top, int bottom) {
        for (int y = 0; y < h; y += 3) {
            Gui.drawRect(0, y, w, Math.min(h, y + 3), lerp(top, bottom, y / (float) h));
        }
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

    /** ساده‌ترین roundRect: چند مستطیل + گوشه‌های مربعی (بدون GL_POLYGON ناپایدار) */
    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        if (w <= 0 || h <= 0) return;
        if (((color >>> 24) & 255) <= 4) return;
        r = Math.min(r, Math.min(w, h) / 2f);
        int ir = (int) Math.ceil(r);
        // middle
        Gui.drawRect((int)x,         (int)(y + r),  (int)(x + w), (int)(y + h - r), color);
        // top + bottom bands
        Gui.drawRect((int)(x + r),   (int)y,        (int)(x + w - r), (int)(y + r),   color);
        Gui.drawRect((int)(x + r),   (int)(y + h - r), (int)(x + w - r), (int)(y + h), color);
        // corners
        for (int i = 0; i < ir; i++) {
            double dy = ir - i - 0.5;
            int inset = (int) Math.round(ir - Math.sqrt(Math.max(0, ir * ir - dy * dy)));
            Gui.drawRect((int)(x + inset),         (int)(y + i),           (int)(x + w - inset), (int)(y + i + 1),         color);
            Gui.drawRect((int)(x + inset),         (int)(y + h - i - 1),   (int)(x + w - inset), (int)(y + h - i),         color);
        }
    }

    public static void roundOutline(float x, float y, float w, float h, float r, float thickness, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        // high-level: چهار خط مستقیم + چهار گوشه
        rect(x + r, y,         w - 2 * r, thickness, color);
        rect(x + r, y + h - thickness, w - 2 * r, thickness, color);
        rect(x,         y + r, thickness, h - 2 * r, color);
        rect(x + w - thickness, y + r, thickness, h - 2 * r, color);
    }

    public static void panel(float x, float y, float w, float h, float r, int fill, int border) {
        if (((fill >>> 24) & 255) > 4) roundRect(x, y, w, h, r, fill);
        if (border != 0 && ((border >>> 24) & 255) > 4) roundOutline(x, y, w, h, r, 1f, border);
    }

    public static void bar(float x, float y, float w, float h, double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2f, bg);
        float fw = (float)(w * Math.max(0, Math.min(1, frac)));
        if (fw > 0) roundRect(x, y, fw, h, h / 2f, fg);
    }

    public static void dashedH(float x, float y, float w, int color) {
        for (int i = 0; i < w; i += 6) rect(x + i, y, Math.min(w - i, 3), 1, color);
    }

    public static void circle(float cx, float cy, float r, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        int ir = (int) Math.ceil(r);
        for (int dy = -ir; dy <= ir; dy++) {
            int half = (int) Math.sqrt(Math.max(0, ir * ir - dy * dy));
            rect(cx - half, cy + dy, half * 2, 1, color);
        }
    }

    public static void line(float x1, float y1, float x2, float y2, float width, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        float dx = x2 - x1, dy = y2 - y1;
        float len = (float) Math.sqrt(dx * dx + dy * dy);
        if (len < 0.01f) return;
        int steps = (int) Math.ceil(len);
        for (int i = 0; i <= steps; i++) {
            float t = i / (float) steps;
            rect(x1 + dx * t - width / 2f, y1 + dy * t - width / 2f, width, width, color);
        }
    }

    public static void glow(float x, float y, float w, float h, float r, int color, float spread) {
        // فقط یک halo ملایم با چند rect — بدون GL polygon
        if (((color >>> 24) & 255) <= 4) return;
        for (int i = 1; i <= (int) spread; i++) {
            int a = (int) (((color >>> 24) & 255) * (1f - i / spread) * 0.08f);
            if (a <= 0) continue;
            roundRect(x - i, y - i, w + i * 2, h + i * 2, r + i, (a << 24) | (color & 0xFFFFFF));
        }
    }

    public static void shadow(float x, float y, float w, float h, float r, int color, float spread) {
        glow(x, y, w, h, r, color, spread);
    }

    public static void radial(float cx, float cy, float r, int color, boolean fill) {
        // approximation - not used heavily in 3.x
        circle(cx, cy, r, color);
    }

    // ---- icons ----
    public static void gear(float cx, float cy, float r, float angle, int color, int hole) {
        GlStateManager.pushMatrix();
        GlStateManager.translate(cx, cy, 0f);
        GlStateManager.rotate(angle, 0f, 0f, 1f);
        roundRect(-r,       -r / 3f, r * 2f, r / 1.5f, 1f, color);
        GlStateManager.rotate(90f, 0f, 0f, 1f);
        roundRect(-r,       -r / 3f, r * 2f, r / 1.5f, 1f, color);
        GlStateManager.rotate(45f, 0f, 0f, 1f);
        roundRect(-r,       -r / 3f, r * 2f, r / 1.5f, 1f, color);
        GlStateManager.rotate(90f, 0f, 0f, 1f);
        roundRect(-r,       -r / 3f, r * 2f, r / 1.5f, 1f, color);
        roundRect(-r * .75f, -r * .75f, r * 1.5f, r * 1.5f, r * 0.75f, color);
        roundRect(-r * .35f, -r * .35f, r * 0.7f, r * 0.7f, r * 0.35f, hole);
        GlStateManager.popMatrix();
    }

    public static void icon(int type, float cx, float cy, float size, int color) {
        float h = size / 2f;
        if (type == ICON_ARROW) {
            for (int i = 0; i < (int) size; i++) {
                float t = i / size;
                rect(cx - h + i, cy - h + i, 1, Math.max(1, (int)(size - i * 2)), color);
            }
        } else if (type == ICON_GEAR) {
            gear(cx, cy, h, 0, color, 0);
        } else {
            rect(cx - h, cy - h, size, size, color);
        }
    }

    // ---- text ----
    public static FontRenderer font() { return Minecraft.getMinecraft().fontRendererObj; }
    public static int width(String s, float scale) { return (int)(font().getStringWidth(s) * scale); }
    public static int w(String s, float scale, boolean bold) { return width(s, scale); }

    /** ارتفاع خط متن در مقیاس داده شده */
    public static float lineH(float scale) { return font().FONT_HEIGHT * scale; }

    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, shadow);
        GlStateManager.popMatrix();
    }

    /** مرکز افقی + مرکز عمودی دقیق با احتساب ارتفاع واقعی فونت */
    public static void centered(String s, float cx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, cx - tw / 2f, cy - th / 2f, color, scale, shadow);
    }

    public static void mid(String s, float cx, float cy, int color, float scale, boolean shadow) {
        centered(s, cx, cy, color, scale, shadow);
    }

    public static void mid(String s, float cx, float cy, int color, float scale) {
        centered(s, cx, cy, color, scale, false);
    }

    public static void left(String s, float x, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float th = font().FONT_HEIGHT * scale;
        text(s, x, cy - th / 2f, color, scale, shadow);
    }

    public static void right(String s, float rx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, rx - tw, cy - th / 2f, color, scale, shadow);
    }

    public static String fit(String s, float maxW, float scale, boolean bold) {
        if (s == null) return "";
        if (w(s, scale, bold) <= maxW) return s;
        String ell = "...";
        while (s.length() > 0 && w(s + ell, scale, bold) > maxW) {
            s = s.substring(0, s.length() - 1);
        }
        return s + ell;
    }

    public static List<String> wrap(String s, float maxW, float scale, boolean bold) {
        List<String> lines = new ArrayList<String>();
        if (s == null || s.isEmpty()) return lines;
        String[] words = s.split(" ");
        StringBuilder cur = new StringBuilder();
        for (String word : words) {
            String test = cur.length() == 0 ? word : cur + " " + word;
            if (w(test, scale, bold) > maxW && cur.length() > 0) {
                lines.add(cur.toString());
                cur = new StringBuilder(word);
            } else {
                cur = new StringBuilder(test);
            }
        }
        if (cur.length() > 0) lines.add(cur.toString());
        return lines;
    }

    public static void plexusBackground(int w, int h, float maxAlpha) {
        // ساده: چند خط محو
        long t = System.currentTimeMillis() / 50L;
        int n = Math.min(60, Math.max(20, (w * h) / 12000));
        for (int i = 0; i < n; i++) {
            float x1 = ((i * 97L + t) % (w + 40)) - 20;
            float y1 = ((i * 53L - t / 2) % (h + 40)) - 20;
            if (y1 < 0) y1 += h + 40;
            float x2 = ((i * 71L + t * 2) % (w + 40)) - 20;
            float y2 = ((i * 31L - t) % (h + 40)) - 20;
            if (y2 < 0) y2 += h + 40;
            line(x1, y1, x2, y2, 1f, alpha(Theme.accent(), maxAlpha * 0.35f));
        }
    }
}
''')


# ===========================================================================
# 5) GuiModernMenu.java — چیدمان ریسپانسیو، بدون هم‌پوشانی متن
# ===========================================================================
write(UI / "GuiModernMenu.java", r'''package com.oryvex.kbclient.ui;

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

        sidebarW = Math.max(180, Math.min(320, (int)(this.width * 0.28f)));

        int padding = Math.max(12, sidebarW / 10);
        int bw = sidebarW - padding * 2;
        int bh = Math.max(20, Math.min(28, this.height / 20));
        int gap = Math.max(4, bh / 6);

        int totalH = 6 * bh + 5 * gap;
        int top = Math.max(96, (this.height - totalH) / 2 + 20);

        this.buttonList.add(new UiButton(1, padding, top, bw, bh, "Singleplayer").delay(80));
        this.buttonList.add(new UiButton(2, padding, top + (bh + gap), bw, bh, "Multiplayer").delay(120));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap), bw, bh, "Alt Manager").delay(160));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap), bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(200));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap), bw, bh, "Options").icon(UiButton.ICON_GEAR).delay(240));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap), bw, bh, "Quit").style(UiButton.DANGER).delay(280));
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
                closeThen(new Runnable() { @Override public void run() { mc.shutdown(); } });
                break;
            default: break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        // main menu : ESC غیرفعال
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);

        // -------- Sidebar --------
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // -------- Title --------
        float titleScale = Math.max(1.4f, Math.min(2.4f, sidebarW / 130f));
        String title = "ORYVEX";
        Draw.centered(title, sidebarW / 2f, 50f, Theme.TEXT, titleScale, true);

        float subScale = 0.85f;
        Draw.centered("KB Client v" + KBClientMod.VERSION, sidebarW / 2f, 50f + Draw.lineH(titleScale) + 4f,
                Theme.ACCENT, subScale, false);

        Draw.rect(20, 50 + Draw.lineH(titleScale) + Draw.lineH(subScale) + 12, sidebarW - 40, 1, Theme.BORDER);

        // -------- Profile widget (بالا-راست) --------
        KBProfile p = tracker.getProfile();
        if (p.hasData && this.width > sidebarW + 120) {
            String s = "Profile:  " + p.summary();
            int w = Draw.width(s, 0.85f) + 34;
            int px = this.width - w - 14;
            int py = 14;
            Draw.roundRect(px, py, w, 22, 6f, Theme.PANEL2);
            Draw.roundOutline(px, py, w, 22, 6f, 1f, Theme.BORDER);
            Draw.circle(px + 12, py + 11, 3.5f, Theme.GOOD);
            Draw.left(s, px + 22, py + 11, Theme.TEXT, 0.85f, false);
        }

        // -------- User card (پایین sidebar) --------
        int userY = this.height - 28;
        Draw.rect(20, userY - 14, sidebarW - 40, 1, Theme.BORDER);

        Draw.roundRect(20, userY - 8, 18, 18, 9f, Theme.PANEL3);
        Draw.centered("L", 29, userY + 1, Theme.SOFT, 1.0f, false);

        Draw.text("Logged in as", 44, userY - 4, Theme.MUTED, 0.75f, false);
        String name = mc.getSession().getUsername();
        String nameF = Draw.fit(name, sidebarW - 56, 0.95f, false);
        Draw.text(nameF, 44, userY + 4, Theme.TEXT, 0.95f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
''')


# ===========================================================================
# 6) GuiKbOptions.java — چیدمان مرکزی با ارتفاع متن واقعی (بدون هم‌پوشانی)
# ===========================================================================
write(UI / "GuiKbOptions.java", r'''package com.oryvex.kbclient.ui;

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
        int bw = Math.min(260, this.width - 60);
        int bh = 22;
        int gap = 6;
        int cx = this.width / 2;

        // ارتفاع کارت: عنوان (40) + 6 ردیف + دکمه‌ها + footer
        int rows = 6;
        int innerH = rows * (bh + gap) + gap + 2 * (bh + gap) + 8;
        cardW = bw + 40;
        cardH = innerH + 70;
        cardX = cx - cardW / 2;
        cardY = Math.max(20, (this.height - cardH) / 2);

        int y = cardY + 58;
        int bx = cx - bw / 2;

        bHud   = new UiButton(1, bx, y, bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(60);
        bPart  = new UiButton(2, bx, y + 1 * (bh + gap), bw, bh, "Menu particles").style(UiButton.TOGGLE).delay(100);
        bToast = new UiButton(3, bx, y + 2 * (bh + gap), bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(140);
        bLoad  = new UiButton(4, bx, y + 3 * (bh + gap), bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(180);
        bDisc  = new UiButton(8, bx, y + 4 * (bh + gap), bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(220);
        bFade  = new UiButton(5, bx, y + 5 * (bh + gap), bw, bh, "").delay(260);

        this.buttonList.add(bHud);
        this.buttonList.add(bPart);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bDisc);
        this.buttonList.add(bFade);

        int y2 = y + 6 * (bh + gap) + 10;
        this.buttonList.add(new UiButton(6, bx, y2, bw, bh, "Minecraft Options...").icon(UiButton.ICON_GEAR).delay(300));
        this.buttonList.add(new UiButton(7, bx, y2 + bh + gap, bw, bh, "Done").style(UiButton.PRIMARY).delay(340));

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
        drawBackdrop(mouseX, mouseY);
        Draw.panel(cardX, cardY, cardW, cardH, 8, Theme.GLASS, Theme.BORDER);

        float cx = this.width / 2f;

        Draw.centered("OPTIONS", cx, cardY + 22, Theme.TEXT, 1.6f, true);
        Draw.centered("KB Client preferences", cx, cardY + 42, Theme.MUTED, 0.85f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
''')


# ===========================================================================
# 7) Hud.java — رفع هم‌پوشانی متن، درست‌کردن ارتفاع‌ها
# ===========================================================================
write(UI / "Hud.java", r'''package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBSample;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.ScaledResolution;

public final class Hud {
    private Hud() {}

    private static final class Toast {
        final String text;
        final int color;
        final long born;
        Toast(String t, int c) { text = t; color = c; born = System.currentTimeMillis(); }
    }

    private static final List<Toast> toasts = new ArrayList<Toast>();
    private static float alpha = 0f;
    private static long lastNs = System.nanoTime();

    public static void push(String text, int color) {
        if (!Settings.toasts) return;
        toasts.add(new Toast(text, color));
        while (toasts.size() > 4) toasts.remove(0);
    }

    public static void render(Minecraft mc, KBTracker t) {
        ScaledResolution res = new ScaledResolution(mc);
        Draw.blend();
        if (Settings.watermark) {
            Draw.right("Created by muvixo", res.getScaledWidth() - 4,
                    res.getScaledHeight() - 6, Theme.DIM, 0.7f, false);
        }

        long ns = System.nanoTime();
        float dt = Math.min(0.1f, (ns - lastNs) / 1.0e9f);
        lastNs = ns;
        alpha += ((Settings.hud ? 1f : 0f) - alpha) * Math.min(1f, dt * 8f);
        if (alpha < 0.03f) return;
        float a = alpha;

        KBProfile pr = t.getProfile();
        KBSample last = t.getLast();
        boolean goal = t.getGoal() > 0;
        int x = 6, y = 6, w = 156;
        int h = goal ? 58 : 50;

        Draw.panel(x, y, w, h, 5f, Draw.fade(0xE6101826, a), Draw.fade(Theme.BORDER, a));
        Draw.rect(x + 1, y + 1, 2, h - 2, Draw.fade(t.isRecording() ? Theme.accent() : Theme.DIM, a));

        // Header
        Draw.left("KB CLIENT", x + 8, y + 10, Draw.fade(Theme.accent(), a), 0.8f, false);
        Draw.right(t.isRecording() ? "REC" : "PAUSED", x + w - 6, y + 10,
                Draw.fade(t.isRecording() ? Theme.GOOD : Theme.WARN, a), 0.8f, false);

        // Stats
        if (last != null) {
            Draw.left("H " + KBProfile.f(last.h, 4) + "   V " + KBProfile.f(last.vy, 4),
                    x + 8, y + 24, Draw.fade(Theme.TEXT, a), 0.9f, false);
        } else {
            Draw.left("Waiting for hits...", x + 8, y + 24, Draw.fade(Theme.MUTED, a), 0.9f, false);
        }
        Draw.left(pr.used + " / " + pr.total + " samples", x + 8, y + 36,
                Draw.fade(Theme.MUTED, a), 0.75f, false);

        // Confidence pips
        for (int i = 0; i < KBProfile.COUNT; i++) {
            int c = pr.src[i] == KBProfile.SRC_NONE ? Theme.PANEL3 : Draw.confColor(pr.conf[i]);
            Draw.rect(x + 8 + i * 11, y + 44, 9, 2, Draw.fade(c, a));
        }
        if (goal) {
            Draw.bar(x + 8, y + h - 10, w - 16, 3,
                    t.getSessionHits() / (double) t.getGoal(),
                    Draw.fade(Theme.PANEL3, a), Draw.fade(Theme.accent(), a));
        }

        // Toasts زیر HUD
        long now = System.currentTimeMillis();
        for (int i = toasts.size() - 1; i >= 0; i--) {
            if (now - toasts.get(i).born > 3600) toasts.remove(i);
        }
        int ty = y + h + 4;
        for (int i = toasts.size() - 1; i >= 0; i--) {
            Toast to = toasts.get(i);
            long age = now - to.born;
            float in   = age < 160 ? age / 160f : 1f;
            float fade = (age > 2800 ? 1f - (age - 2800) / 800f : 1f) * in * a;
            int tw = Draw.width(to.text, 0.85f) + 14;
            Draw.roundRect(x, ty, tw, 14, 3f, Draw.alpha(0x101826, 0.85f * fade));
            int al = (int)(255 * fade);
            if (al > 4) Draw.left(to.text, x + 7, ty + 7, (al << 24) | (to.color & 0xFFFFFF), 0.85f, false);
            ty += 16;
        }
        Draw.blend();
    }
}
''')


# ===========================================================================
# 8) LoadingArt.java — ساده‌سازی برای جلوگیری از polygon ناپایدار
# ===========================================================================
write(UI / "LoadingArt.java", r'''package com.oryvex.kbclient.ui;

public final class LoadingArt {
    private LoadingArt() {}

    private static final String[] TIPS = {
        "Press Right Shift in-game to open the Knockback Analyzer.",
        "Get hit by a walking AND a sprinting player to separate HORIZONTAL from EXTRA-HORIZONTAL.",
        "Get hit while falling to measure VERTICAL when Y-LIMIT clamps it.",
        "Use /kb import to compare a Carbon YAML against your detected profile.",
        "Every value in the analyzer carries a source tag: MEAS, EST, DEF or FILE."
    };

    public static void draw(int w, int h, String title, String sub, int pct) {
        Draw.blend();
        Draw.vgradient(w, h, Theme.BG0, Theme.BG1);

        int cx = w / 2;
        int cy = h / 2;
        float t = (System.currentTimeMillis() % 100000L) / 1000f;

        // ---------- Logo ----------
        String logo = "ORYVEX";
        float scale = 3f;
        float tw = Draw.font().getStringWidth(logo) * scale;
        Draw.text(logo, cx - tw / 2f, cy - 90, Theme.TEXT, scale, true);

        Draw.centered("K N O C K B A C K   C L I E N T", cx, cy - 90 + Draw.lineH(scale) + 6,
                Theme.MUTED, 0.85f, false);

        // ---------- Spinner ----------
        int sy = cy + 4;
        Draw.roundRect(cx - 16, sy - 16, 32, 32, 16, Draw.alpha(Theme.accent(), 0.08f));
        for (int i = 0; i < 12; i++) {
            double ang = t * 3.4 - i * 0.5;
            int dx = (int) Math.round(Math.cos(ang) * 13);
            int dy = (int) Math.round(Math.sin(ang) * 13);
            float fa = 1f - i / 12f;
            int sz = i < 3 ? 3 : 2;
            Draw.rect(cx + dx - sz / 2f, sy + dy - sz / 2f, sz, sz,
                    Draw.alpha(i % 2 == 0 ? Theme.accent() : Theme.accent2(), fa));
        }

        // ---------- Status text ----------
        String ttl = (title == null || title.isEmpty()) ? "Loading" : title;
        Draw.centered(ttl, cx, cy + 40, Theme.TEXT, 1.0f, true);
        if (sub != null && !sub.isEmpty()) {
            Draw.centered(sub, cx, cy + 40 + Draw.lineH(1.0f) + 4, Theme.MUTED, 0.85f, false);
        }

        // ---------- Bar ----------
        int bw = 180, bx = cx - bw / 2, by = cy + 76;
        Draw.roundRect(bx, by, bw, 4, 2, Theme.PANEL3);
        if (pct >= 0) {
            Draw.roundRect(bx, by, Math.max(2, bw * Math.min(100, pct) / 100), 4, 2, Theme.accent());
            Draw.centered(pct + "%", cx, by + 12, Theme.SOFT, 0.8f, false);
        } else {
            float p = (t * 0.9f) % 1f;
            int seg = 56;
            int sx = bx + (int)((bw + seg) * p) - seg;
            int x0 = Math.max(bx, sx);
            int x1 = Math.min(bx + bw, sx + seg);
            if (x1 > x0) Draw.roundRect(x0, by, x1 - x0, 4, 2, Theme.accent());
        }

        // ---------- Tip ----------
        String tip = "TIP  " + TIPS[(int)((System.currentTimeMillis() / 4500L) % TIPS.length)];
        Draw.centered(tip, cx, h - 22, Theme.DIM, 0.85f, false);
        Draw.left("KB Client 3.0", 6, h - 10, Theme.DIM, 0.75f, false);
        Draw.right("Created by muvixo", w - 6, h - 10, Theme.DIM, 0.75f, false);
    }
}
''')


# ===========================================================================
# 9) UiButton — استفاده‌ی درست از Draw.centered (بدون 4f*scale قدیمی)
# ===========================================================================
write(UI / "UiButton.java", r'''package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import org.lwjgl.input.Mouse;

public class UiButton extends GuiButton {
    public static final int NORMAL = 0, PRIMARY = 1, DANGER = 2, TAB = 3, TOGGLE = 4, GHOST = 5;
    public static final int ICON_NONE = Draw.ICON_NONE, ICON_GEAR = Draw.ICON_GEAR;

    public int style = NORMAL;
    public int icon = ICON_NONE;
    public boolean selected;
    public boolean on;
    public long delay;
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
        if (!enabled) ap *= 0.55f;

        float inset = pr * 0.9f;
        float x = xPosition + inset;
        float y = yPosition + inset + (1f - ap) * 7f;
        float w = width - inset * 2f;
        float h = height - inset * 2f;
        float r = Math.min(h / 2f, style == TAB ? 4f : 7f);
        float cy = y + h / 2f;

        int accent = Theme.accent();
        int accent2 = Theme.accent2();
        int textCol;

        switch (style) {
            case PRIMARY: {
                int c1 = Draw.lerp(Draw.shade(accent, 0.86f), accent, hv);
                int c2 = Draw.lerp(Draw.shade(accent2, 0.86f), accent2, hv);
                Draw.roundRect(x, y, w, h, r, Draw.fade(c1, ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(0x55FFFFFF, ap * (0.5f + 0.5f * hv)));
                textCol = Ui.onAccent();
                break;
            }
            case DANGER: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, 0x55FB7185, hv), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Theme.BAD, hv), ap));
                textCol = Draw.lerp(Draw.lerp(Theme.SOFT, Theme.BAD, 0.4f), 0xFFFFFFFF, hv * 0.6f);
                break;
            }
            case TAB: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(selected ? Theme.FILL : Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            case TOGGLE: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv * 0.8f), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.7f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, Math.max(hv, kn * 0.7f));
                break;
            }
            case GHOST: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            default: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.75f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
            }
        }

        textCol = Draw.fade(textCol, ap);

        if (style == TOGGLE) {
            Draw.left(Draw.fit(displayString, w - 48f, textSize, false), x + 10f, cy, textCol, textSize, false);
            Ui.toggle(x + w - 10f - 24f, cy, kn, ap);
            return;
        }

        float isz = Math.min(11f, h - 8f);
        boolean hasIcon = icon != ICON_NONE;
        String label = Draw.fit(displayString, w - (hasIcon ? isz + 22f : 16f), textSize, false);
        float tw = Draw.w(label, textSize, false);
        float startX;
        if (left) startX = x + 12f;
        else      startX = x + (w - (tw + (hasIcon ? isz + 6f : 0f))) / 2f;

        if (hasIcon) {
            float ix = startX + isz / 2f;
            int ic = style == PRIMARY ? textCol
                    : Draw.fade(Draw.lerp(Draw.lerp(Theme.MUTED, Theme.SOFT, 0.5f),
                            Draw.lerp(accent, 0xFFFFFFFF, 0.25f), hv), ap);
            if (style == DANGER) ic = Draw.fade(Draw.lerp(Theme.BAD, 0xFFFFFFFF, hv * 0.5f), ap);
            if (icon == ICON_GEAR) Draw.gear(ix, cy, isz * 1.15f, spin, ic, 0);
            else Draw.icon(icon, ix, cy, isz * 1.15f, ic);
            startX += isz + 6f;
        }

        if (left) {
            Draw.left(label, startX, cy, textCol, textSize, style == PRIMARY);
        } else {
            Draw.centered(label, x + w / 2f, cy, textCol, textSize, style == PRIMARY);
        }

        if (style == TAB && selected) {
            Draw.roundRect(x + 8f, y + h - 2f, w - 16f, 2f, 1f, Draw.fade(accent, ap));
        }
    }
}
''')


# ===========================================================================
# 10) Ui.java — بدون تغییر، فقط برای اطمینان
# ===========================================================================
write(UI / "Ui.java", r'''package com.oryvex.kbclient.ui;

import java.util.List;

public final class Ui {
    private Ui() {}

    public static int onAccent() {
        int c = Theme.accentMid();
        float lum = (0.299f * ((c >> 16) & 255) + 0.587f * ((c >> 8) & 255) + 0.114f * (c & 255)) / 255f;
        return lum > 0.66f ? 0xFF0A0C14 : 0xFFFFFFFF;
    }

    public static void toggle(float x, float cy, float knob, float alpha) {
        float w = 24f, h = 12f, y = cy - h / 2f;
        int off = Draw.fade(0x38FFFFFF, alpha);
        int c1 = Draw.lerp(off, Draw.fade(Theme.accent(), alpha), knob);
        int c2 = Draw.lerp(off, Draw.fade(Theme.accent2(), alpha), knob);
        Draw.roundRect(x, y, w, h, h / 2f, c1);
        Draw.circle(x + 6f + (w - 12f) * knob, cy, 4.2f, Draw.fade(0xFFFFFFFF, alpha));
    }

    public static void slider(float x, float cy, float w, float frac, boolean active, float alpha) {
        frac = Draw.clamp(frac);
        Draw.roundRect(x, cy - 2f, w, 4f, 2f, Draw.fade(0x30FFFFFF, alpha));
        float fw = Math.max(4f, w * frac);
        Draw.roundRect(x, cy - 2f, fw, 4f, 2f, Draw.fade(Theme.accent(), alpha));
        float kx = x + w * frac;
        Draw.circle(kx, cy, active ? 5.4f : 4.6f, Draw.fade(0xFFFFFFFF, alpha));
    }

    public static float chip(String text, float x, float cy, float size, int bg, int fg, boolean bold) {
        float tw = Draw.w(text, size, bold);
        float h = size * 9 + 5f;
        float w = tw + 10f;
        Draw.roundRect(x, cy - h / 2f, w, h, h / 2f, bg);
        Draw.centered(text, x + w / 2f, cy, fg, size, bold);
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
        float maxW = Math.min(180f, sw - 20f);
        List<String> lines = Draw.wrap(body, maxW, Theme.T_SM, false);
        float tw = title == null ? 0 : Draw.w(title, Theme.T_MD, true);
        for (String l : lines) tw = Math.max(tw, Draw.w(l, Theme.T_SM, false));
        float w = tw + 16f;
        float h = 10f + (title == null ? 0 : 13f) + lines.size() * (Draw.lineH(Theme.T_SM) + 2f);
        float x = mx + 10f, y = my + 12f;
        if (x + w > sw - 4) x = mx - w - 8f;
        if (y + h > sh - 4) y = my - h - 8f;
        if (x < 4) x = 4;
        if (y < 4) y = 4;
        Draw.panel(x, y, w, h, 5f, 0xF2080A11, Theme.STROKE_HI);
        float ty = y + 8f;
        if (title != null) {
            Draw.left(title, x + 8f, ty + Draw.lineH(Theme.T_MD) / 2f, Theme.TEXT, Theme.T_MD, true);
            ty += 13f;
        }
        for (String l : lines) {
            Draw.left(l, x + 8f, ty + Draw.lineH(Theme.T_SM) / 2f, Theme.SOFT, Theme.T_SM, false);
            ty += Draw.lineH(Theme.T_SM) + 2f;
        }
    }
}
''')


# ===========================================================================
# 11) Anim.java
# ===========================================================================
write(UI / "Anim.java", r'''package com.oryvex.kbclient.ui;

public final class Anim {
    public float v;
    private long last = System.nanoTime();

    public Anim() {}
    public Anim(float start) { v = start; }

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
''')


# ===========================================================================
# 12) KBClientMod — اطمینان از اتصال ModernFontRenderer
# ===========================================================================
MOD = JAVA / "KBClientMod.java"
if MOD.exists():
    txt = MOD.read_text(encoding="utf-8")
    if "ModernFontRenderer" not in txt:
        anchor = "DiscordRPC.start();"
        if anchor in txt:
            inject = (
                anchor + "\n\n"
                "          try {\n"
                "              net.minecraft.client.Minecraft mc2 = net.minecraft.client.Minecraft.getMinecraft();\n"
                "              mc2.fontRendererObj = new com.oryvex.kbclient.font.ModernFontRenderer(\n"
                "                      mc2.gameSettings,\n"
                "                      new net.minecraft.util.ResourceLocation(\"textures/font/ascii.png\"),\n"
                "                      mc2.renderEngine, false);\n"
                "              logger.info(\"[KBClient] ModernFontRenderer attached\");\n"
                "          } catch (Throwable t) {\n"
                "              logger.error(\"[KBClient] ModernFontRenderer failed: \" + t);\n"
                "          }"
            )
            txt = txt.replace(anchor, inject, 1)
            MOD.write_text(txt, encoding="utf-8")
            print("  [PATCH] KBClientMod.java : ModernFontRenderer wired")
        else:
            print("  [WARN ] KBClientMod.java : DiscordRPC.start() not found")


# ===========================================================================
# fonts check
# ===========================================================================
for name in ("Inter-Regular.ttf", "Vazirmatn-Regular.ttf"):
    fp = RES / "fonts" / name
    print(f"  [{'OK' if fp.exists() else 'WARN'}] fonts/{name}")


print("\nDone.  Rebuild:")
print("    ./gradlew clean build")
print("اگر هنوز متن بزرگ دیده می‌شود، این فایل را حذف کن و ری‌استارت کن:")
print("    .minecraft/kbclient/settings.properties")