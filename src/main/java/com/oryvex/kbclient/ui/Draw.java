package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import org.lwjgl.opengl.GL11;

import java.util.ArrayList;
import java.util.List;

/** Immediate-mode drawing toolkit. All icons are vector-based. */
public final class Draw {
    private Draw() {}

    // Icon IDs
    public static final int ICON_NONE    = 0;
    public static final int ICON_GEAR    = 1;
    public static final int ICON_ARROW   = 2;
    public static final int ICON_PLUS    = 3;
    public static final int ICON_MINUS   = 4;
    public static final int ICON_COPY    = 5;
    public static final int ICON_SAVE    = 6;
    public static final int ICON_TRASH   = 7;
    public static final int ICON_REFRESH = 8;
    public static final int ICON_CLOSE   = 9;
    public static final int ICON_CHECK   = 10;
    public static final int ICON_HOME    = 11;
    public static final int ICON_PLAY    = 12;
    public static final int ICON_GRAPH   = 13;
    public static final int ICON_CODE    = 14;
    public static final int ICON_USER    = 15;
    public static final int ICON_STAR    = 16;

    // ---- math ----
    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }
    public static float ease(float t) { t = clamp(t); return t * t * (3f - 2f * t); }
    public static float easeOut(float t) { t = clamp(t); return 1f - (1f - t) * (1f - t); }
    public static float easeInOut(float t) { t = clamp(t); return t < 0.5f ? 2f*t*t : 1f-(float)Math.pow(-2f*t+2f,2f)/2f; }
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

    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        if (w <= 0 || h <= 0) return;
        if (((color >>> 24) & 255) <= 4) return;
        r = Math.min(r, Math.min(w, h) / 2f);
        int ir = (int) Math.ceil(r);
        if (ir <= 0) { Gui.drawRect((int)x, (int)y, (int)(x+w), (int)(y+h), color); return; }
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

    // ---- ICONS (vector, correct size) ----
    /**
     * Draws a vector icon centred at (cx, cy).
     * "size" is the full bounding-box size (diameter for circular icons).
     * Icons never exceed the given size.
     */
    public static void icon(int type, float cx, float cy, float size, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        float h = size / 2f;
        switch (type) {
            case ICON_GEAR:    drawGear(cx, cy, h, 0f, color); break;
            case ICON_ARROW:   drawArrow(cx, cy, h, color); break;
            case ICON_PLUS:    drawPlus(cx, cy, h, color); break;
            case ICON_MINUS:   drawMinus(cx, cy, h, color); break;
            case ICON_CLOSE:   drawClose(cx, cy, h, color); break;
            case ICON_CHECK:   drawCheck(cx, cy, h, color); break;
            case ICON_COPY:    drawCopy(cx, cy, h, color); break;
            case ICON_SAVE:    drawSave(cx, cy, h, color); break;
            case ICON_TRASH:   drawTrash(cx, cy, h, color); break;
            case ICON_REFRESH: drawRefresh(cx, cy, h, color); break;
            case ICON_HOME:    drawHome(cx, cy, h, color); break;
            case ICON_PLAY:    drawPlay(cx, cy, h, color); break;
            case ICON_GRAPH:   drawGraph(cx, cy, h, color); break;
            case ICON_CODE:    drawCode(cx, cy, h, color); break;
            case ICON_USER:    drawUser(cx, cy, h, color); break;
            case ICON_STAR:    drawStar(cx, cy, h, color); break;
            default:           rect(cx - h, cy - h, size, size, color); break;
        }
    }

    /** Rotating gear with 8 teeth, radius r. Bounded to 2r diameter. */
    public static void drawGear(float cx, float cy, float r, float angle, int color) {
        if (r < 0.5f) return;
        float or_ = r;               // tooth tip radius
        float ir  = r * 0.66f;       // body radius
        float tr  = r * 0.22f;       // half tooth width
        int teeth = 8;

        double ar = Math.toRadians(angle);

        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        setGLColor(color);

        // teeth quads (built as two triangles each)
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
            float nx = -dy / len * tr;
            float ny =  dx / len * tr;

            float ex0 = cx + (float)Math.cos(a0) * or_;
            float ey0 = cy + (float)Math.sin(a0) * or_;
            float ex1 = cx + (float)Math.cos(a1) * or_;
            float ey1 = cy + (float)Math.sin(a1) * or_;

            GL11.glBegin(GL11.GL_TRIANGLES);
            GL11.glVertex2f(x0 + nx, y0 + ny);
            GL11.glVertex2f(x1 + nx, y1 + ny);
            GL11.glVertex2f(ex1,      ey1);
            GL11.glEnd();

            GL11.glBegin(GL11.GL_TRIANGLES);
            GL11.glVertex2f(x1 + nx, y1 + ny);
            GL11.glVertex2f(x1 - nx, y1 - ny);
            GL11.glVertex2f(ex1,      ey1);
            GL11.glEnd();

            GL11.glBegin(GL11.GL_TRIANGLES);
            GL11.glVertex2f(x1 - nx, y1 - ny);
            GL11.glVertex2f(x0 - nx, y0 - ny);
            GL11.glVertex2f(ex0,      ey0);
            GL11.glEnd();

            GL11.glBegin(GL11.GL_TRIANGLES);
            GL11.glVertex2f(x0 - nx, y0 - ny);
            GL11.glVertex2f(x0 + nx, y0 + ny);
            GL11.glVertex2f(ex1,      ey1);
            GL11.glEnd();

            GL11.glBegin(GL11.GL_TRIANGLES);
            GL11.glVertex2f(x0 - nx, y0 - ny);
            GL11.glVertex2f(ex1,      ey1);
            GL11.glVertex2f(ex0,      ey0);
            GL11.glEnd();
        }

        // body disc
        GL11.glBegin(GL11.GL_TRIANGLE_FAN);
        GL11.glVertex2f(cx, cy);
        for (int i = 0; i <= 40; i++) {
            double a = ar + (2 * Math.PI * i) / 40;
            GL11.glVertex2f(cx + (float)Math.cos(a) * ir, cy + (float)Math.sin(a) * ir);
        }
        GL11.glEnd();

        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void drawArrow(float cx, float cy, float h, int color) {
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        float w = h * 0.85f;
        GL11.glBegin(GL11.GL_TRIANGLES);
        GL11.glVertex2f(cx - w * 0.55f, cy - h * 0.75f);
        GL11.glVertex2f(cx - w * 0.55f, cy + h * 0.75f);
        GL11.glVertex2f(cx + w * 0.95f, cy);
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void drawPlus(float cx, float cy, float h, int color) {
        float t = Math.max(1f, h * 0.32f);
        rect(cx - h,      cy - t / 2f, h * 2f, t, color);
        rect(cx - t / 2f, cy - h,      t, h * 2f, color);
    }

    private static void drawMinus(float cx, float cy, float h, int color) {
        float t = Math.max(1f, h * 0.32f);
        rect(cx - h, cy - t / 2f, h * 2f, t, color);
    }

    private static void drawClose(float cx, float cy, float h, int color) {
        float t = Math.max(1.2f, h * 0.28f);
        line(cx - h, cy - h, cx + h, cy + h, t, color);
        line(cx + h, cy - h, cx - h, cy + h, t, color);
    }

    private static void drawCheck(float cx, float cy, float h, int color) {
        float t = Math.max(1.2f, h * 0.28f);
        line(cx - h,       cy,        cx - h * 0.3f, cy + h * 0.7f, t, color);
        line(cx - h * 0.3f, cy + h * 0.7f, cx + h,    cy - h * 0.75f, t, color);
    }

    private static void drawCopy(float cx, float cy, float h, int color) {
        float t = Math.max(1f, h * 0.18f);
        roundOutline(cx - h * 0.55f, cy - h * 0.85f, h * 1.05f, h * 1.35f, 2f, t, color);
        roundOutline(cx - h * 0.15f, cy - h * 0.4f,  h * 1.05f, h * 1.35f, 2f, t, color);
    }

    private static void drawSave(float cx, float cy, float h, int color) {
        float t = Math.max(1f, h * 0.18f);
        roundOutline(cx - h * 0.85f, cy - h * 0.85f, h * 1.7f, h * 1.7f, 2f, t, color);
        rect(cx - h * 0.45f, cy - h * 0.85f, h * 0.9f, h * 0.55f, color);
        rect(cx - h * 0.55f, cy + h * 0.15f, h * 1.1f, h * 0.65f, color);
    }

    private static void drawTrash(float cx, float cy, float h, int color) {
        rect(cx - h * 0.7f, cy - h * 0.4f, h * 1.4f, h * 1.25f, color);
        rect(cx - h * 0.85f, cy - h * 0.7f, h * 1.7f, h * 0.2f, color);
        rect(cx - h * 0.3f,  cy - h * 0.95f, h * 0.6f, h * 0.2f, color);
    }

    private static void drawRefresh(float cx, float cy, float h, int color) {
        float t = Math.max(1.2f, h * 0.22f);
        int segs = 20;
        for (int i = 0; i < segs; i++) {
            double a0 = -Math.PI * 0.35 + (i / (double)segs) * (Math.PI * 1.7);
            double a1 = -Math.PI * 0.35 + ((i + 1) / (double)segs) * (Math.PI * 1.7);
            float x0 = cx + (float)Math.cos(a0) * h * 0.7f;
            float y0 = cy + (float)Math.sin(a0) * h * 0.7f;
            float x1 = cx + (float)Math.cos(a1) * h * 0.7f;
            float y1 = cy + (float)Math.sin(a1) * h * 0.7f;
            line(x0, y0, x1, y1, t, color);
        }
        // arrow head
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        float ah = h * 0.4f;
        float ax = cx + h * 0.7f;
        float ay = cy - h * 0.1f;
        GL11.glBegin(GL11.GL_TRIANGLES);
        GL11.glVertex2f(ax - ah * 0.5f, ay - ah);
        GL11.glVertex2f(ax + ah * 0.5f, ay - ah);
        GL11.glVertex2f(ax,             ay + ah * 0.4f);
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void drawHome(float cx, float cy, float h, int color) {
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        GL11.glBegin(GL11.GL_TRIANGLES);
        GL11.glVertex2f(cx,          cy - h);
        GL11.glVertex2f(cx - h,      cy);
        GL11.glVertex2f(cx + h,      cy);
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
        rect(cx - h * 0.65f, cy, h * 1.3f, h * 0.85f, color);
    }

    private static void drawPlay(float cx, float cy, float h, int color) {
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        GL11.glBegin(GL11.GL_TRIANGLES);
        GL11.glVertex2f(cx - h * 0.55f, cy - h * 0.8f);
        GL11.glVertex2f(cx - h * 0.55f, cy + h * 0.8f);
        GL11.glVertex2f(cx + h * 0.85f, cy);
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void drawGraph(float cx, float cy, float h, int color) {
        float t = Math.max(1f, h * 0.18f);
        float base = cy + h * 0.85f;
        rect(cx - h * 0.75f, cy - h * 0.4f,  h * 0.35f, h * 1.25f, color);
        rect(cx - h * 0.15f, cy - h * 0.85f, h * 0.35f, h * 1.7f,  color);
        rect(cx + h * 0.45f, cy - h * 0.2f,  h * 0.35f, h * 1.05f, color);
        rect(cx - h * 0.85f, base, h * 1.7f, t, color);
    }

    private static void drawCode(float cx, float cy, float h, int color) {
        float t = Math.max(1.2f, h * 0.22f);
        line(cx - h * 0.2f, cy - h * 0.7f,  cx - h * 0.85f, cy,          t, color);
        line(cx - h * 0.85f, cy,             cx - h * 0.2f, cy + h * 0.7f, t, color);
        line(cx + h * 0.2f, cy - h * 0.7f,  cx + h * 0.85f, cy,          t, color);
        line(cx + h * 0.85f, cy,             cx + h * 0.2f, cy + h * 0.7f, t, color);
    }

    private static void drawUser(float cx, float cy, float h, int color) {
        circle(cx, cy - h * 0.4f, h * 0.38f, color);
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        GL11.glBegin(GL11.GL_TRIANGLE_FAN);
        GL11.glVertex2f(cx, cy + h * 0.55f);
        for (int i = 0; i <= 24; i++) {
            double a = Math.PI + (Math.PI * i) / 24;
            GL11.glVertex2f(cx + (float)Math.cos(a) * h * 0.75f, cy + h * 0.75f + (float)Math.sin(a) * h * 0.55f);
        }
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void drawStar(float cx, float cy, float h, int color) {
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        GL11.glBegin(GL11.GL_TRIANGLE_FAN);
        GL11.glVertex2f(cx, cy);
        for (int i = 0; i <= 10; i++) {
            double a = -Math.PI / 2 + (Math.PI * 2 * i) / 10;
            float rr = (i % 2 == 0) ? h : h * 0.42f;
            GL11.glVertex2f(cx + (float)Math.cos(a) * rr, cy + (float)Math.sin(a) * rr);
        }
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void setGLColor(int color) {
        float r = ((color >> 16) & 255) / 255f;
        float g = ((color >> 8)  & 255) / 255f;
        float b = ( color        & 255) / 255f;
        float a = ((color >>> 24)      ) / 255f;
        GlStateManager.color(r, g, b, a);
    }

    // ---- text ----
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

    /** Radial gradient approximation: soft circle fading to transparent. */
    public static void radial(float cx, float cy, float r, int color, boolean fill) {
        if (((color >>> 24) & 255) <= 4) return;
        int steps = Math.max(3, (int) r / 4);
        for (int i = steps; i >= 1; i--) {
            float t = i / (float) steps;
            float rr = r * t;
            int a = (int) (((color >>> 24) & 255) * (1f - t) * 0.5f);
            if (a <= 0) continue;
            circle(cx, cy, rr, (a << 24) | (color & 0xFFFFFF));
        }
        circle(cx, cy, r, color);
    }

    /** Soft drop shadow behind a rounded rect. */
    public static void shadow(float x, float y, float w, float h, float r, int color, float spread) {
        if (((color >>> 24) & 255) <= 4) return;
        for (int i = 1; i <= (int) spread; i++) {
            int a = (int) (((color >>> 24) & 255) * (1f - i / spread) * 0.10f);
            if (a <= 0) continue;
            roundRect(x - i, y - i + 1f, w + i * 2f, h + i * 2f, r + i,
                      (a << 24) | (color & 0xFFFFFF));
        }
    }

}
