package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;

/** Small immediate-mode drawing toolkit (rounded panels, bars, text, particles). */
public final class Draw {
    private Draw() {}

    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }

    public static int lerp(int a, int b, float t) {
        t = clamp(t);
        int aa = (a >>> 24) & 255, ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
        int ba = (b >>> 24) & 255, br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;
        int ra = (int) (aa + (ba - aa) * t);
        int rr = (int) (ar + (br - ar) * t);
        int rg = (int) (ag + (bg - ag) * t);
        int rb = (int) (ab + (bb - ab) * t);
        return (ra << 24) | (rr << 16) | (rg << 8) | rb;
    }

    public static int alpha(int color, float a) {
        int al = (int) (clamp(a) * 255f);
        return (al << 24) | (color & 0xFFFFFF);
    }

    /** red -> yellow -> green */
    public static int confColor(double c) {
        float f = (float) Math.max(0, Math.min(1, c));
        return f < 0.5f ? lerp(Theme.BAD, Theme.WARN, f * 2f) : lerp(Theme.WARN, Theme.GOOD, (f - 0.5f) * 2f);
    }

    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void rect(int x, int y, int w, int h, int color) {
        Gui.drawRect(x, y, x + w, y + h, color);
    }

    public static void roundRect(int x, int y, int w, int h, int r, int color) {
        if (w <= 0 || h <= 0) return;
        r = Math.min(r, Math.min(w, h) / 2);
        if (r <= 0) { Gui.drawRect(x, y, x + w, y + h, color); return; }
        Gui.drawRect(x, y + r, x + w, y + h - r, color);
        for (int i = 0; i < r; i++) {
            double dy = r - i - 0.5;
            int inset = (int) Math.round(r - Math.sqrt(r * r - dy * dy));
            Gui.drawRect(x + inset, y + i, x + w - inset, y + i + 1, color);
            Gui.drawRect(x + inset, y + h - i - 1, x + w - inset, y + h - i, color);
        }
    }

    /** rounded panel with 1px border */
    public static void panel(int x, int y, int w, int h, int r, int fill, int border) {
        roundRect(x, y, w, h, r, border);
        roundRect(x + 1, y + 1, w - 2, h - 2, Math.max(0, r - 1), fill);
    }

    public static void bar(int x, int y, int w, int h, double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2, bg);
        int fw = (int) (w * Math.max(0, Math.min(1, frac)));
        if (fw > 0) roundRect(x, y, fw, h, h / 2, fg);
    }

    public static void dashedH(int x, int y, int w, int color) {
        for (int i = 0; i < w; i += 6) Gui.drawRect(x + i, y, x + Math.min(w, i + 3), y + 1, color);
    }

    // ---- text -------------------------------------------------------------
    public static FontRenderer font() { return Minecraft.getMinecraft().fontRendererObj; }

    public static int width(String s, float scale) { return (int) (font().getStringWidth(s) * scale); }

    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, shadow);
        GlStateManager.popMatrix();
    }

    public static void centered(String s, float cx, float y, int color, float scale, boolean shadow) {
        text(s, cx - font().getStringWidth(s) * scale / 2f, y, color, scale, shadow);
    }

    public static void right(String s, float rx, float y, int color, float scale, boolean shadow) {
        text(s, rx - font().getStringWidth(s) * scale, y, color, scale, shadow);
    }

    // ---- ambient particles -------------------------------------------------
    private static float hash(int n) {
        double v = Math.sin(n * 12.9898) * 43758.5453;
        return (float) (v - Math.floor(v));
    }

    private static float mod(float a, float m) {
        float r = a % m;
        return r < 0 ? r + m : r;
    }

    public static void particles(int w, int h, int count, int rgb, float maxAlpha) {
        float t = (System.currentTimeMillis() % 1000000L) / 1000f;
        for (int i = 0; i < count; i++) {
            float r1 = hash(i * 3 + 1), r2 = hash(i * 3 + 2), r3 = hash(i * 3 + 3);
            float sp = 4f + r3 * 14f;
            float x = mod(r1 * w + t * sp * 0.6f, w);
            float y = mod(r2 * h - t * sp, h);
            float tw = 0.5f + 0.5f * (float) Math.sin(t * (0.6f + r3 * 1.5f) + i);
            int a = (int) (maxAlpha * 255f * tw * (0.4f + 0.6f * r3));
            int sz = r3 > 0.8f ? 2 : 1;
            Gui.drawRect((int) x, (int) y, (int) x + sz, (int) y + sz, (a << 24) | (rgb & 0xFFFFFF));
        }
    }
}
