package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;

import java.util.ArrayList;
import java.util.List;

/** Minimal immediate-mode drawing toolkit. Icons have been removed. */
public final class Draw {
    private Draw() {}

    /* icon ids exist only so old source still compiles */
    public static final int ICON_NONE  = 0;
    public static final int ICON_GEAR  = 1;
    public static final int ICON_ARROW = 2;
    public static final int ICON_PLUS  = 3;
    public static final int ICON_MINUS = 4;
    public static final int ICON_CLOSE = 5;
    public static final int ICON_CHECK = 6;
    public static final int ICON_PLAY  = 7;
    public static final int ICON_GRAPH = 8;
    public static final int ICON_USER  = 9;
    public static final int ICON_HOME  = 10;
    public static final int ICON_STAR  = 11;
    public static final int ICON_TRASH = 12;
    public static final int ICON_COPY  = 13;
    public static final int ICON_SAVE  = 14;

    /* ---------------- math helpers ---------------- */
    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }

    public static float ease(float t) {
        t = clamp(t);
        return t * t * (3f - 2f * t);
    }

    public static float easeOut(float t) {
        t = clamp(t);
        float u = 1f - t;
        return 1f - u * u * u;
    }

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

    public static int confColor(double c) {
        float f = (float) Math.max(0, Math.min(1, c));
        return f < 0.5f ? lerp(Theme.BAD, Theme.WARN, f * 2f)
                        : lerp(Theme.WARN, Theme.GOOD, (f - 0.5f) * 2f);
    }

    /* ---------------- GL state ---------------- */
    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void resetColor() {
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.disableBlend();
    }

    /* ---------------- primitives ---------------- */
    public static void rect(float x, float y, float w, float h, int color) {
        Gui.drawRect((int) x, (int) y, (int)(x + w), (int)(y + h), color);
    }

    public static void vgradient(int w, int h, int top, int bottom) { rect(0, 0, w, h, top); }

    public static void vgrad(float x, float y, float w, float h, int top, int bottom) {
        rect(x, y, w, h, top);
    }

    public static void hgrad(float x, float y, float w, float h, int left, int right) {
        rect(x, y, w, h, left);
    }

    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        if (w <= 0f || h <= 0f) return;
        if (((color >>> 24) & 255) <= 4) return;
        r = Math.min(r, Math.min(w, h) / 2f);
        int ir = (int) Math.ceil(r);
        if (ir <= 0) {
            Gui.drawRect((int) x, (int) y, (int)(x + w), (int)(y + h), color);
            return;
        }
        Gui.drawRect((int) x,       (int)(y + r),     (int)(x + w),     (int)(y + h - r), color);
        Gui.drawRect((int)(x + r),  (int) y,          (int)(x + w - r), (int)(y + r),     color);
        Gui.drawRect((int)(x + r),  (int)(y + h - r), (int)(x + w - r), (int)(y + h),     color);
        for (int i = 0; i < ir; i++) {
            double dy = ir - i - 0.5;
            int inset = (int) Math.round(ir - Math.sqrt(Math.max(0, ir * ir - dy * dy)));
            Gui.drawRect((int)(x + inset), (int)(y + i),
                         (int)(x + w - inset), (int)(y + i + 1), color);
            Gui.drawRect((int)(x + inset), (int)(y + h - i - 1),
                         (int)(x + w - inset), (int)(y + h - i), color);
        }
    }

    public static void roundOutline(float x, float y, float w, float h,
                                    float r, float t, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        rect(x + r,     y,         w - 2 * r, t, color);
        rect(x + r,     y + h - t, w - 2 * r, t, color);
        rect(x,         y + r,     t, h - 2 * r, color);
        rect(x + w - t, y + r,     t, h - 2 * r, color);
    }

    public static void panel(float x, float y, float w, float h,
                             float r, int fill, int border) {
        if (((fill >>> 24) & 255) > 4) roundRect(x, y, w, h, r, fill);
        if (border != 0 && ((border >>> 24) & 255) > 4)
            roundOutline(x, y, w, h, r, 1f, border);
    }

    public static void bar(float x, float y, float w, float h,
                           double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2f, bg);
        float fw = (float)(w * Math.max(0, Math.min(1, frac)));
        if (fw > 0f) roundRect(x, y, fw, h, h / 2f, fg);
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

    public static void dashedH(float x, float y, float w, int color) {
        if (w <= 0f || ((color >>> 24) & 255) <= 4) return;
        for (float i = 0f; i < w; i += 6f) {
            int x0 = (int)(x + i);
            int x1 = (int)(x + Math.min(w, i + 3f));
            Gui.drawRect(x0, (int) y, x1, (int) y + 1, color);
        }
    }

    public static void dashedV(float x, float y, float h, int color) {
        if (h <= 0f || ((color >>> 24) & 255) <= 4) return;
        for (float i = 0f; i < h; i += 6f) {
            int y0 = (int)(y + i);
            int y1 = (int)(y + Math.min(h, i + 3f));
            Gui.drawRect((int) x, y0, (int) x + 1, y1, color);
        }
    }

    /* ---------------- icons are a no-op ---------------- */
    public static void icon(int type, float cx, float cy, float size, int color) { }

    /* ---------------- text ---------------- */
    public static FontRenderer font() {
        try {
            com.oryvex.kbclient.font.ModernFontRenderer mf =
                    com.oryvex.kbclient.KBClientMod.modernFont;
            if (mf != null) return mf;
        } catch (Throwable ignored) {
            // fall through to vanilla font
        }
        return Minecraft.getMinecraft().fontRendererObj;
    }

    public static int width(String s, float scale) {
        return (int)(font().getStringWidth(s) * scale);
    }

    public static int w(String s, float scale, boolean bold) {
        return width(s, scale);
    }

    public static float lineH(float scale) {
        return font().FONT_HEIGHT * scale;
    }

    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, false);
        GlStateManager.popMatrix();
    }

    public static void centered(String s, float cx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, cx - tw / 2f, cy - th / 2f, color, scale, false);
    }

    public static void mid(String s, float cx, float cy, int color, float scale, boolean shadow) {
        centered(s, cx, cy, color, scale, false);
    }

    public static void mid(String s, float cx, float cy, int color, float scale) {
        centered(s, cx, cy, color, scale, false);
    }

    public static void left(String s, float x, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float th = font().FONT_HEIGHT * scale;
        text(s, x, cy - th / 2f, color, scale, false);
    }

    public static void right(String s, float rx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, rx - tw, cy - th / 2f, color, scale, false);
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
}
