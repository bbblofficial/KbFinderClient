package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import java.util.ArrayList;
import java.util.List;

public final class Draw {
    private Draw() {}

    public static final int ICON_NONE = 0, ICON_GEAR = 1, ICON_ARROW = 2;

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

    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void resetColor() {
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.disableBlend();
    }

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

    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        if (w <= 0 || h <= 0) return;
        if (((color >>> 24) & 255) <= 4) return;
        r = Math.min(r, Math.min(w, h) / 2f);
        int ir = (int) Math.ceil(r);
        Gui.drawRect((int)x,       (int)(y + r), (int)(x + w), (int)(y + h - r), color);
        Gui.drawRect((int)(x + r), (int)y,       (int)(x + w - r), (int)(y + r),   color);
        Gui.drawRect((int)(x + r), (int)(y + h - r), (int)(x + w - r), (int)(y + h), color);
        for (int i = 0; i < ir; i++) {
            double dy = ir - i - 0.5;
            int inset = (int) Math.round(ir - Math.sqrt(Math.max(0, ir * ir - dy * dy)));
            Gui.drawRect((int)(x + inset), (int)(y + i),         (int)(x + w - inset), (int)(y + i + 1),   color);
            Gui.drawRect((int)(x + inset), (int)(y + h - i - 1), (int)(x + w - inset), (int)(y + h - i),   color);
        }
    }

    public static void roundOutline(float x, float y, float w, float h, float r, float t, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        rect(x + r, y,             w - 2 * r, t, color);
        rect(x + r, y + h - t,     w - 2 * r, t, color);
        rect(x,             y + r, t, h - 2 * r, color);
        rect(x + w - t,     y + r, t, h - 2 * r, color);
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
        circle(cx, cy, r, color);
    }

    /**
     * Pixel-perfect vector gear icon, drawn with GL lines + triangles.
     * Looks the same at any size — the old roundRect-based version broke
     * on small buttons (see issue with Options button).
     */
    public static void gear(float cx, float cy, float r, float angle, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        if (r < 1.5f) return;

        float or = r;          // outer radius (tooth tip)
        float ir = r * 0.62f;  // inner radius (body)
        float tr = r * 0.28f;  // tooth width
        int teeth = 8;

        float ar = (float) Math.toRadians(angle);

        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);

        float rr = ((color >> 16) & 255) / 255f;
        float gg = ((color >> 8)  & 255) / 255f;
        float bb = ( color        & 255) / 255f;
        float aa = ((color >>> 24)      ) / 255f;
        GlStateManager.color(rr, gg, bb, aa);

        // --- teeth as quads ---
        for (int i = 0; i < teeth; i++) {
            double a0 = ar + (2 * Math.PI * i) / teeth;
            double a1 = a0 + (2 * Math.PI / teeth) * 0.55;

            float x0 = cx + (float)Math.cos(a0) * ir;
            float y0 = cy + (float)Math.sin(a0) * ir;
            float x1 = cx + (float)Math.cos(a1) * ir;
            float y1 = cy + (float)Math.sin(a1) * ir;

            float dx = x1 - x0, dy = y1 - y0;
            float len = (float)Math.sqrt(dx * dx + dy * dy);
            if (len < 0.001f) continue;
            float nx = -dy / len * (tr * 0.5f);
            float ny =  dx / len * (tr * 0.5f);

            float tx0 = x0 + nx, ty0 = y0 + ny;
            float tx1 = x1 + nx, ty1 = y1 + ny;
            float tx2 = x1 - nx, ty2 = y1 - ny;
            float tx3 = x0 - nx, ty3 = y0 - ny;

            float ex0 = cx + (float)Math.cos(a0) * or;
            float ey0 = cy + (float)Math.sin(a0) * or;
            float ex1 = cx + (float)Math.cos(a1) * or;
            float ey1 = cy + (float)Math.sin(a1) * or;

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx0, ty0);
            org.lwjgl.opengl.GL11.glVertex2f(tx1, ty1);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx1, ty1);
            org.lwjgl.opengl.GL11.glVertex2f(tx2, ty2);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx2, ty2);
            org.lwjgl.opengl.GL11.glVertex2f(tx3, ty3);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx3, ty3);
            org.lwjgl.opengl.GL11.glVertex2f(tx0, ty0);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();
        }

        // --- inner disc ---
        org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_TRIANGLE_FAN);
        org.lwjgl.opengl.GL11.glVertex2f(cx, cy);
        for (int i = 0; i <= 32; i++) {
            double a = ar + (2 * Math.PI * i) / 32;
            org.lwjgl.opengl.GL11.glVertex2f(
                cx + (float)Math.cos(a) * ir,
                cy + (float)Math.sin(a) * ir);
        }
        org.lwjgl.opengl.GL11.glEnd();

        // --- centre hole ---
        int bg = 0;
        try {
            bg = (org.lwjgl.opengl.GL11.glGetInteger(org.lwjgl.opengl.GL11.GL_BLEND) != 0) ? 0x00000000 : 0x00000000;
        } catch (Throwable ignored) {}
        org.lwjgl.opengl.GL11.glColor4f(0f, 0f, 0f, 0f);
        org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_TRIANGLE_FAN);
        org.lwjgl.opengl.GL11.glVertex2f(cx, cy);
        for (int i = 0; i <= 24; i++) {
            double a = (2 * Math.PI * i) / 24;
            org.lwjgl.opengl.GL11.glVertex2f(
                cx + (float)Math.cos(a) * (r * 0.24f),
                cy + (float)Math.sin(a) * (r * 0.24f));
        }
        org.lwjgl.opengl.GL11.glEnd();

        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    /** Legacy signature (angle + hole). Kept so old callers keep compiling. */
    public static void gear(float cx, float cy, float r, float angle, int color, int hole) {
        gear(cx, cy, r, angle, color);
    }

    public static void icon(int type, float cx, float cy, float size, int color) {
        float h = size / 2f;
        if (type == ICON_ARROW) {
            GlStateManager.disableTexture2D();
            GlStateManager.enableBlend();
            float rr = ((color >> 16) & 255) / 255f;
            float gg = ((color >> 8)  & 255) / 255f;
            float bb = ( color        & 255) / 255f;
            float aa = ((color >>> 24)      ) / 255f;
            GlStateManager.color(rr, gg, bb, aa);
            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_TRIANGLES);
            org.lwjgl.opengl.GL11.glVertex2f(cx - h * 0.6f, cy - h);
            org.lwjgl.opengl.GL11.glVertex2f(cx - h * 0.6f, cy + h);
            org.lwjgl.opengl.GL11.glVertex2f(cx + h * 0.9f, cy);
            org.lwjgl.opengl.GL11.glEnd();
            GlStateManager.color(1f, 1f, 1f, 1f);
            GlStateManager.enableTexture2D();
        } else if (type == ICON_GEAR) {
            gear(cx, cy, h, 0, color);
        } else {
            rect(cx - h, cy - h, size, size, color);
        }
    }

    /** فونت UI ما: ModernFontRenderer اگر آماده باشد، وگرنه vanilla */
    public static FontRenderer font() {
        try {
            com.oryvex.kbclient.font.ModernFontRenderer mf = com.oryvex.kbclient.KBClientMod.modernFont;
            if (mf != null) return mf;
        } catch (Throwable ignored) { }
        return Minecraft.getMinecraft().fontRendererObj;
    }

    public static int width(String s, float scale) { return (int)(font().getStringWidth(s) * scale); }
    public static int w(String s, float scale, boolean bold) { return width(s, scale); }
    public static float lineH(float scale) { return font().FONT_HEIGHT * scale; }

    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, shadow);
        GlStateManager.popMatrix();
    }

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
