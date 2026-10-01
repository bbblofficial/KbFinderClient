import os

# Define the content for the fixed files
files_to_modify = {
    "src/main/java/com/oryvex/kbclient/ui/Theme.java": """package com.oryvex.kbclient.ui;

/** Flat colour palette. Simplified for clarity. */
public final class Theme {
    private Theme() {}

    // ---- backgrounds ----
    public static final int BG0   = 0xFF0A0E14;
    public static final int BG1   = 0xFF11161F;

    // ---- surfaces ----
    public static final int SURFACE   = 0xFF161B24;
    public static final int SURFACE2  = 0xFF1D232E;
    public static final int SURFACE3  = 0xFF252C38;
    
    // Legacy aliases for compatibility
    public static final int PANEL   = SURFACE;
    public static final int PANEL2  = SURFACE2;
    public static final int PANEL3  = SURFACE3;
    public static final int GLASS   = SURFACE;

    public static final int BORDER    = 0xFF2A323E;
    public static final int BORDER_HI = 0xFF3A4453;

    // ---- status ----
    public static final int GOOD = 0xFF4ADE80;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD  = 0xFFF87171;

    // ---- text ----
    public static final int TEXT  = 0xFFF1F5F9;
    public static final int SOFT  = 0xFFCBD5E1;
    public static final int MUTED = 0xFF94A3B8;
    public static final int DIM   = 0xFF64748B;

    // ---- accent ----
    public static final int ACCENT    = 0xFF3B82F6;
    public static final int ACCENT_DK = 0xFF1E40AF;
    public static final int ACCENT2   = 0xFFA78BFA; // Secondary accent (Purple)

    // ---- Typography Scale ----
    public static final float T_XS = 0.75f;
    public static final float T_SM = 0.85f;
    public static final float T_MD = 1.00f;
    public static final float T_LG = 1.25f;
    public static final float T_XL = 1.60f;

    public static final String S = "\\u00a7";
}""",

    "src/main/java/com/oryvex/kbclient/ui/Draw.java": """package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import org.lwjgl.opengl.GL11;

import java.util.ArrayList;
import java.util.List;

/** Minimal drawing toolkit: rectangles, borders, lines, text, vector icons. */
public final class Draw {
    private Draw() {}

    // ---- Icon IDs ----
    public static final int ICON_NONE    = 0;
    public static final int ICON_GEAR    = 1;
    public static final int ICON_ARROW   = 2;
    public static final int ICON_PLUS    = 3;
    public static final int ICON_MINUS   = 4;
    public static final int ICON_CLOSE   = 5;
    public static final int ICON_CHECK   = 6;
    public static final int ICON_PLAY    = 7;
    public static final int ICON_GRAPH   = 8;
    public static final int ICON_USER    = 9;
    public static final int ICON_HOME    = 10;
    public static final int ICON_STAR    = 11;
    public static final int ICON_TRASH   = 12;
    public static final int ICON_COPY    = 13;
    public static final int ICON_SAVE    = 14;

    // ---- math helpers ----
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
        // flat background — ignore gradient, draw solid
        rect(0, 0, w, h, top);
    }

    public static void vgrad(float x, float y, float w, float h, int top, int bottom) {
        rect(x, y, w, h, top);
    }

    public static void hgrad(float x, float y, float w, float h, int left, int right) {
        rect(x, y, w, h, left);
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
            Gui.drawRect((int)(x + inset), (int)(y + i),         (int)(x + w - inset), (int)(y + i + 1), color);
            Gui.drawRect((int)(x + inset), (int)(y + h - i - 1), (int)(x + w - inset), (int)(y + h - i), color);
        }
    }

    /** Thin 1px outline drawn on top of a rounded rect. */
    public static void roundOutline(float x, float y, float w, float h, float r, float t, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        rect(x + r, y,             w - 2 * r, t, color);
        rect(x + r, y + h - t,     w - 2 * r, t, color);
        rect(x,             y + r, t, h - 2 * r, color);
        rect(x + w - t,     y + r, t, h - 2 * r, color);
    }

    /** Flat panel: fill + 1px border. */
    public static void panel(float x, float y, float w, float h, float r, int fill, int border) {
        if (((fill >>> 24) & 255) > 4) roundRect(x, y, w, h, r, fill);
        if (border != 0 && ((border >>> 24) & 255) > 4) roundOutline(x, y, w, h, r, 1f, border);
    }

    public static void bar(float x, float y, float w, float h, double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2f, bg);
        float fw = (float)(w * Math.max(0, Math.min(1, frac)));
        if (fw > 0) roundRect(x, y, fw, h, h / 2f, fg);
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

    // ---- Icons (flat vector, no glow) ----
    public static void icon(int type, float cx, float cy, float size, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        float h = size / 2f;
        switch (type) {
            case ICON_GEAR:  drawGear(cx, cy, h, 0f, color); break;
            case ICON_ARROW: drawTriangle(cx + h * 0.15f, cy, h, color, 1); break;
            case ICON_PLAY:  drawTriangle(cx + h * 0.15f, cy, h, color, 1); break;
            case ICON_PLUS:  drawPlus(cx, cy, h, color); break;
            case ICON_MINUS: rect(cx - h, cy - Math.max(1f, h * 0.15f), h * 2f, Math.max(1.5f, h * 0.3f), color); break;
            case ICON_CLOSE: drawClose(cx, cy, h, color); break;
            case ICON_CHECK: drawCheck(cx, cy, h, color); break;
            case ICON_GRAPH: drawGraph(cx, cy, h, color); break;
            case ICON_USER:  drawUser(cx, cy, h, color); break;
            case ICON_HOME:  drawHome(cx, cy, h, color); break;
            case ICON_STAR:  drawStar(cx, cy, h, color); break;
            case ICON_TRASH: drawTrash(cx, cy, h, color); break;
            case ICON_COPY:  drawCopy(cx, cy, h, color); break;
            case ICON_SAVE:  drawSave(cx, cy, h, color); break;
            default:         rect(cx - h, cy - h, size, size, color); break;
        }
    }

    private static void drawGear(float cx, float cy, float r, float angle, int color) {
        if (r < 0.5f) return;
        float or_ = r, ir = r * 0.66f, tr = r * 0.22f;
        int teeth = 8;
        double ar = Math.toRadians(angle);
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
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
            float nx = -dy / len * tr, ny = dx / len * tr;
            float ex0 = cx + (float)Math.cos(a0) * or_;
            float ey0 = cy + (float)Math.sin(a0) * or_;
            float ex1 = cx + (float)Math.cos(a1) * or_;
            float ey1 = cy + (float)Math.sin(a1) * or_;
            GL11.glBegin(GL11.GL_QUADS);
            GL11.glVertex2f(x0 + nx, y0 + ny);
            GL11.glVertex2f(x1 + nx, y1 + ny);
            GL11.glVertex2f(ex1, ey1);
            GL11.glVertex2f(ex0, ey0);
            GL11.glEnd();
        }
        GL11.glBegin(GL11.GL_TRIANGLE_FAN);
        GL11.glVertex2f(cx, cy);
        for (int i = 0; i <= 32; i++) {
            double a = ar + (2 * Math.PI * i) / 32;
            GL11.glVertex2f(cx + (float)Math.cos(a) * ir, cy + (float)Math.sin(a) * ir);
        }
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void drawTriangle(float cx, float cy, float h, int color, int dir) {
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        GL11.glBegin(GL11.GL_TRIANGLES);
        if (dir == 1) {
            GL11.glVertex2f(cx - h * 0.55f, cy - h * 0.85f);
            GL11.glVertex2f(cx - h * 0.55f, cy + h * 0.85f);
            GL11.glVertex2f(cx + h * 0.85f, cy);
        } else {
            GL11.glVertex2f(cx + h * 0.55f, cy - h * 0.85f);
            GL11.glVertex2f(cx + h * 0.55f, cy + h * 0.85f);
            GL11.glVertex2f(cx - h * 0.85f, cy);
        }
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    private static void drawPlus(float cx, float cy, float h, int color) {
        float t = Math.max(2f, h * 0.32f);
        rect(cx - h,      cy - t / 2f, h * 2f, t, color);
        rect(cx - t / 2f, cy - h,      t, h * 2f, color);
    }

    private static void drawClose(float cx, float cy, float h, int color) {
        float t = Math.max(1.6f, h * 0.26f);
        line(cx - h * 0.85f, cy - h * 0.85f, cx + h * 0.85f, cy + h * 0.85f, t, color);
        line(cx + h * 0.85f, cy - h * 0.85f, cx - h * 0.85f, cy + h * 0.85f, t, color);
    }

    private static void drawCheck(float cx, float cy, float h, int color) {
        float t = Math.max(1.6f, h * 0.26f);
        line(cx - h * 0.85f, cy,               cx - h * 0.2f, cy + h * 0.7f, t, color);
        line(cx - h * 0.2f,  cy + h * 0.7f,    cx + h * 0.85f, cy - h * 0.7f, t, color);
    }

    private static void drawGraph(float cx, float cy, float h, int color) {
        float bw = h * 0.32f;
        rect(cx - h * 0.85f, cy - h * 0.15f, bw, h * 1.0f, color);
        rect(cx - bw * 0.5f, cy - h * 0.75f, bw, h * 1.6f, color);
        rect(cx + h * 0.55f, cy - h * 0.45f, bw, h * 1.3f, color);
    }

    private static void drawUser(float cx, float cy, float h, int color) {
        circle(cx, cy - h * 0.35f, h * 0.35f, color);
        float bodyY = cy + h * 0.15f;
        rect(cx - h * 0.7f, bodyY, h * 1.4f, h * 0.7f, color);
    }

    private static void drawHome(float cx, float cy, float h, int color) {
        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        setGLColor(color);
        GL11.glBegin(GL11.GL_TRIANGLES);
        GL11.glVertex2f(cx, cy - h * 0.9f);
        GL11.glVertex2f(cx - h * 0.85f, cy);
        GL11.glVertex2f(cx + h * 0.85f, cy);
        GL11.glEnd();
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
        rect(cx - h * 0.6f, cy, h * 1.2f, h * 0.85f, color);
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

    private static void drawTrash(float cx, float cy, float h, int color) {
        rect(cx - h * 0.65f, cy - h * 0.4f, h * 1.3f, h * 1.2f, color);
        rect(cx - h * 0.85f, cy - h * 0.7f, h * 1.7f, h * 0.2f, color);
        rect(cx - h * 0.3f,  cy - h * 0.95f, h * 0.6f, h * 0.2f, color);
    }

    private static void drawCopy(float cx, float cy, float h, int color) {
        float t = Math.max(1f, h * 0.16f);
        roundOutline(cx - h * 0.55f, cy - h * 0.85f, h * 1.05f, h * 1.35f, 2f, t, color);
        roundOutline(cx - h * 0.15f, cy - h * 0.4f,  h * 1.05f, h * 1.35f, 2f, t, color);
    }

    private static void drawSave(float cx, float cy, float h, int color) {
        float t = Math.max(1f, h * 0.16f);
        roundOutline(cx - h * 0.85f, cy - h * 0.85f, h * 1.7f, h * 1.7f, 2f, t, color);
        rect(cx - h * 0.4f, cy - h * 0.85f, h * 0.8f, h * 0.5f, color);
        rect(cx - h * 0.55f, cy + h * 0.15f, h * 1.1f, h * 0.6f, color);
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

    /* ------------------------------------------------------------------ */
    /*  Dashed rules (restored — the Graph tab and section headers use them) */
    /* ------------------------------------------------------------------ */
    /** Dashed horizontal rule from (x, y) with length w. */
    public static void dashedH(float x, float y, float w, int color) {
        if (w <= 0f || ((color >>> 24) & 255) <= 4) return;
        for (float i = 0f; i < w; i += 6f) {
            int x0 = (int) (x + i);
            int x1 = (int) (x + Math.min(w, i + 3f));
            Gui.drawRect(x0, (int) y, x1, (int) y + 1, color);
        }
    }

    /** Dashed vertical rule from (x, y) with length h. */
    public static void dashedV(float x, float y, float h, int color) {
        if (h <= 0f || ((color >>> 24) & 255) <= 4) return;
        for (float i = 0f; i < h; i += 6f) {
            int y0 = (int) (y + i);
            int y1 = (int) (y + Math.min(h, i + 3f));
            Gui.drawRect((int) x, y0, (int) x + 1, y1, color);
        }
    }
}""",

    "src/main/java/com/oryvex/kbclient/ui/UiButton.java": """package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;

/** Simple flat button. No glow, no press animation. */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public static final int GHOST   = 5;

    // legacy aliases
    public static final int ICON_NONE = Draw.ICON_NONE;
    public static final int ICON_GEAR = Draw.ICON_GEAR;

    public int style = NORMAL;
    public int icon = Draw.ICON_NONE;
    public boolean selected;
    public boolean on;
    public long delay;
    public boolean left;
    public float textSize = Theme.T_MD;

    private final Anim hover = new Anim();
    private final long born = System.currentTimeMillis();

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

        boolean act = this.hovered && this.enabled;
        float hv = hover.to(act ? 1f : 0f, 22f);
        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 260f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.5f;

        float x = xPosition;
        float y = yPosition + (1f - ap) * 6f;
        float w = width;
        float h = height;
        float r = 6f;
        float cy = y + h / 2f;

        int bg;
        int border;
        int textCol;

        switch (style) {
            case PRIMARY:
                bg     = Draw.lerp(Theme.ACCENT_DK, Theme.ACCENT, hv);
                border = Theme.ACCENT;
                textCol = 0xFFFFFFFF;
                break;
            case DANGER:
                bg     = Draw.lerp(0x18FB7185, 0x40FB7185, hv);
                border = Draw.lerp(0x44FB7185, Theme.BAD, hv);
                textCol = Draw.lerp(0xFFFCA5A5, 0xFFFFFFFF, hv);
                break;
            case TAB:
                bg     = selected ? Theme.SURFACE2 : Draw.lerp(0x00FFFFFF, Theme.SURFACE2, hv);
                border = selected ? Theme.BORDER_HI : Theme.BORDER;
                textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            case TOGGLE:
                bg     = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv);
                border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv);
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
                break;
            case GHOST:
                bg     = Draw.lerp(0x00FFFFFF, Theme.SURFACE2, hv);
                border = 0;
                textCol = Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            default:
                bg     = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv);
                border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv);
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
        }

        bg = Draw.fade(bg, ap);
        border = Draw.fade(border, ap);
        textCol = Draw.fade(textCol, ap);

        Draw.roundRect(x, y, w, h, r, bg);
        if (((border >>> 24) & 255) > 4) Draw.roundOutline(x, y, w, h, r, 1f, border);

        if (style == TOGGLE) {
            float sw = 22f, sh = 12f;
            float sx = x + w - sw - 10f;
            Draw.left(Draw.fit(displayString, w - sw - 26f, textSize, false),
                    x + 12f, cy, textCol, textSize, false);
            drawToggle(sx, cy - sh / 2f, sw, sh, Draw.lerp(0f, 1f,
                    (on ? 1f : 0f)), ap);
            return;
        }

        boolean hasIcon = icon != Draw.ICON_NONE;
        float iconSize = Math.min(h * 0.5f, 12f);
        float gap = 8f;
        String label = Draw.fit(displayString,
                w - (hasIcon ? iconSize + gap + 20f : 20f), textSize, false);
        float tw = Draw.w(label, textSize, false);
        float contentW = hasIcon ? iconSize + gap + tw : tw;
        float startX = left ? x + 12f : x + (w - contentW) / 2f;

        if (hasIcon) {
            float icx = startX + iconSize / 2f;
            Draw.icon(icon, icx, cy, iconSize, textCol);
            startX += iconSize + gap;
        }

        Draw.left(label, startX, cy, textCol, textSize, false);

        if (style == TAB && selected) {
            Draw.rect(x + 8f, y + h - 2f, w - 16f, 2f, Theme.ACCENT);
        }
    }

    private void drawToggle(float sx, float sy, float sw, float sh, float knob, float ap) {
        int track = on ? Theme.ACCENT : 0x30FFFFFF;
        Draw.roundRect(sx, sy, sw, sh, sh / 2f, Draw.fade(track, ap));
        float kx = sx + sh / 2f + (sw - sh) * knob;
        Draw.circle(kx, sy + sh / 2f, sh / 2f - 1.5f, Draw.fade(0xFFFFFFFF, ap));
    }
}"""
}

def apply_changes():
    print("Applying simpler design changes...")
    
    # Modify files
    for path, content in files_to_modify.items():
        full_path = os.path.join(".", path)
        if os.path.exists(full_path):
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {path}")
        else:
            print(f"Warning: File not found: {path}")

    print("Changes applied successfully.")

if __name__ == "__main__":
    apply_changes()