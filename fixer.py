#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fixer_clean.py — حذف کامل shader/glow/shadow/particle
و ساخت طراحی ساده و مدرن flat
- فقط solid color + 1px border + گوشه گرد
- بدون radial, glow, shadow, aurora, plexus, particles
- فونت ModernFontRenderer دست‌نخورده
- آیکون‌های برداری درست (بدون glow)
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
    sys.exit("Project root not found.")


ROOT = find_root()
JAVA = ROOT / "src" / "main" / "java" / "com" / "oryvex" / "kbclient"
UI   = JAVA / "ui"
FONT = JAVA / "font"

for d in (UI, FONT):
    d.mkdir(parents=True, exist_ok=True)


def write(path: Path, body: str):
    path.write_text(body, encoding="utf-8")
    print(f"  [WRITE] {path.relative_to(ROOT)}")


# ===========================================================================
# 1) Theme.java — پالت رنگ ساده و flat
# ===========================================================================
write(UI / "Theme.java", r'''package com.oryvex.kbclient.ui;

/** Flat colour palette. No gradients, no glows. */
public final class Theme {
    private Theme() {}

    // ---- backgrounds ----
    public static final int BG0   = 0xFF0A0E14;
    public static final int BG1   = 0xFF11161F;

    // ---- surfaces ----
    public static final int SURFACE   = 0xFF161B24;   // main panels
    public static final int SURFACE2  = 0xFF1D232E;   // raised cards
    public static final int SURFACE3  = 0xFF252C38;   // hovered
    public static final int BORDER    = 0xFF2A323E;   // 1px outline
    public static final int BORDER_HI = 0xFF3A4453;   // hovered outline

    // ---- legacy aliases ----
    public static final int PANEL   = 0xFF161B24;
    public static final int PANEL2  = 0xFF1D232E;
    public static final int PANEL3  = 0xFF252C38;
    public static final int GLASS   = 0xFF161B24;
    public static final int FILL    = 0x14FFFFFF;
    public static final int FILL_HI = 0x22FFFFFF;
    public static final int STROKE  = 0x1FFFFFFF;
    public static final int STROKE_HI = 0x33FFFFFF;

    // ---- status ----
    public static final int GOOD = 0xFF4ADE80;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD  = 0xFFF87171;

    // ---- text ----
    public static final int TEXT  = 0xFFF1F5F9;
    public static final int SOFT  = 0xFFCBD5E1;
    public static final int MUTED = 0xFF94A3B8;
    public static final int DIM   = 0xFF64748B;

    // ---- type scale ----
    public static final float T_XS = 0.75f;
    public static final float T_SM = 0.85f;
    public static final float T_MD = 1.00f;
    public static final float T_LG = 1.25f;
    public static final float T_XL = 1.60f;

    public static final String S = "\u00a7";

    // ---- single accent (flat) ----
    public static final int ACCENT    = 0xFF3B82F6;   // blue
    public static final int ACCENT_HI = 0xFF60A5FA;
    public static final int ACCENT_DK = 0xFF1E40AF;
    public static final int ACCENT2   = 0xFF3B82F6;

    public static String[] THEME_NAMES = { "Blue" };

    public static int accent()  { return ACCENT; }
    public static int accent2() { return ACCENT; }
    public static int accentMid() { return ACCENT; }
    public static int flow(float offset) { return ACCENT; }
    public static float phase() { return 0f; }
}
''')


# ===========================================================================
# 2) Draw.java — فقط primitive های ساده. بدون glow/shadow/radial/plexus
# ===========================================================================
write(UI / "Draw.java", r'''package com.oryvex.kbclient.ui;

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
            GL11.glBegin(GL11.GL_QUADS);
            GL11.glVertex2f(x1 + nx, y1 + ny);
            GL11.glVertex2f(x1 - nx, y1 - ny);
            GL11.glVertex2f(ex1, ey1);
            GL11.glVertex2f(ex0, ey0);
            GL11.glEnd();
            GL11.glBegin(GL11.GL_QUADS);
            GL11.glVertex2f(x1 - nx, y1 - ny);
            GL11.glVertex2f(x0 - nx, y0 - ny);
            GL11.glVertex2f(ex1, ey1);
            GL11.glVertex2f(ex0, ey0);
            GL11.glEnd();
            GL11.glBegin(GL11.GL_QUADS);
            GL11.glVertex2f(x0 - nx, y0 - ny);
            GL11.glVertex2f(x0 + nx, y0 + ny);
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
}
''')


# ===========================================================================
# 3) Background.java — فقط رنگ solid، بدون aurora و particle
# ===========================================================================
write(UI / "Background.java", r'''package com.oryvex.kbclient.ui;

/** Simple flat background — solid colour only. */
public final class Background {
    private Background() {}

    public static void draw(int w, int h, int mx, int my, boolean inWorld, float intensity) {
        Draw.rect(0, 0, w, h, Theme.BG0);
    }
}
''')


# ===========================================================================
# 4) UiButton.java — ساده و flat با hover واضح
# ===========================================================================
write(UI / "UiButton.java", r'''package com.oryvex.kbclient.ui;

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
}
''')


# ===========================================================================
# 5) Anim.java — ساده
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
    public void set(float x) { v = x; last = System.nanoTime(); }
}
''')


# ===========================================================================
# 6) Ui.java — بدون glow
# ===========================================================================
write(UI / "Ui.java", r'''package com.oryvex.kbclient.ui;

public final class Ui {
    private Ui() {}

    public static int onAccent() { return 0xFFFFFFFF; }

    public static void toggle(float x, float cy, float knob, float alpha) {
        float w = 22f, h = 12f, y = cy - h / 2f;
        int track = (knob > 0.5f) ? Theme.ACCENT : 0x30FFFFFF;
        Draw.roundRect(x, y, w, h, h / 2f, Draw.fade(track, alpha));
        float kx = x + h / 2f + (w - h) * knob;
        Draw.circle(kx, cy, h / 2f - 1.5f, Draw.fade(0xFFFFFFFF, alpha));
    }

    public static float chip(String text, float x, float cy, float size, int bg, int fg, boolean bold) {
        float tw = Draw.w(text, size, bold);
        float h = size * 9 + 6f;
        float w = tw + 12f;
        Draw.roundRect(x, cy - h / 2f, w, h, h / 2f, bg);
        Draw.centered(text, x + w / 2f, cy, fg, size, bold);
        return w;
    }
}
''')


# ===========================================================================
# 7) Settings.java — حذف aurora/density
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
''')


# ===========================================================================
# 8) Fade.java / FadeScreen.java — بدون تغییر زیاد، فقط fade پیش‌فرض کوتاه
# ===========================================================================
FADE = UI / "Fade.java"
if FADE.exists():
    t = FADE.read_text(encoding="utf-8")
    t = t.replace("case 1: return 140L;", "case 1: return 80L;")
    t = t.replace("case 2: return 260L;", "case 2: return 160L;")
    t = t.replace("default: return 420L;", "default: return 260L;")
    FADE.write_text(t, encoding="utf-8")
    print(f"  [PATCH] {FADE.relative_to(ROOT)}")


# ===========================================================================
# 9) GuiModernMenu.java — layout ساده و flat
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
        sidebarW = Math.max(200, Math.min(320, (int)(this.width * 0.30f)));

        int padding = 22;
        int bw = sidebarW - padding * 2;
        int bh = 26;
        int gap = 8;
        int totalH = 6 * bh + 5 * gap;
        int top = Math.max(110, (this.height - totalH) / 2 + 16);

        this.buttonList.add(new UiButton(1, padding, top,                   bw, bh, "Singleplayer").icon(Draw.ICON_PLAY).delay(40));
        this.buttonList.add(new UiButton(2, padding, top + 1 * (bh + gap),  bw, bh, "Multiplayer").icon(Draw.ICON_GRAPH).delay(70));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap),  bw, bh, "Alt Manager").icon(Draw.ICON_USER).delay(100));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap),  bw, bh, "Analyzer").style(UiButton.PRIMARY).icon(Draw.ICON_GEAR).delay(130));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap),  bw, bh, "Options").icon(Draw.ICON_GEAR).delay(160));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap),  bw, bh, "Quit").style(UiButton.DANGER).icon(Draw.ICON_CLOSE).delay(190));
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: closeTo(new GuiSelectWorld(this)); break;
            case 2: closeTo(new GuiMultiplayer(this)); break;
            case 3: closeTo(new GuiAnalyzer(tracker, this)); break;
            case 4: closeTo(new GuiKbOptions(tracker, this)); break;
            case 6: closeTo(new GuiAltManager(this)); break;
            case 5: closeThen(new Runnable() { @Override public void run() { mc.shutdown(); } }); break;
            default: break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException { }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);
        Draw.rect(0, 0, sidebarW, this.height, Theme.SURFACE);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // ---- Title ----
        float titleScale = Math.max(1.5f, Math.min(2.2f, sidebarW / 140f));
        Draw.centered("ORYVEX", sidebarW / 2f, 52f, Theme.TEXT, titleScale, false);

        float subScale = 0.85f;
        Draw.centered("KB Client v" + KBClientMod.VERSION, sidebarW / 2f,
                52f + Draw.lineH(titleScale) + 6f, Theme.MUTED, subScale, false);

        float divY = 52f + Draw.lineH(titleScale) + Draw.lineH(subScale) + 16f;
        Draw.rect(sidebarW * 0.2f, divY, sidebarW * 0.6f, 1f, Theme.BORDER);

        // ---- Profile chip (top-right) ----
        KBProfile p = tracker.getProfile();
        if (p.hasData && this.width > sidebarW + 160) {
            String s = p.summary();
            int w = Draw.width(s, 0.85f) + 46;
            int px = this.width - w - 18;
            int py = 18;
            Draw.roundRect(px, py, w, 26, 6f, Theme.SURFACE2);
            Draw.roundOutline(px, py, w, 26, 6f, 1f, Theme.BORDER);
            Draw.circle(px + 14, py + 13, 4f, Theme.GOOD);
            Draw.left("Profile", px + 26, py + 8, Theme.MUTED, 0.72f, false);
            Draw.left(s,       px + 26, py + 18, Theme.TEXT, 0.85f, false);
        }

        // ---- User card (bottom-left) ----
        int userY = this.height - 34;
        Draw.rect(sidebarW * 0.2f, userY - 18, sidebarW * 0.6f, 1f, Theme.BORDER);

        int avX = 22, avY = userY - 8;
        Draw.roundRect(avX, avY, 22, 22, 11f, Theme.SURFACE3);
        Draw.icon(Draw.ICON_USER, avX + 11f, avY + 11f, 12f, Theme.SOFT);

        Draw.left("Logged in as", 52, userY - 2, Theme.MUTED, 0.72f, false);
        String name = mc.getSession().getUsername();
        String nameF = Draw.fit(name, sidebarW - 70, 0.9f, false);
        Draw.left(nameF, 52, userY + 8, Theme.TEXT, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
''')


# ===========================================================================
# 10) GuiKbOptions.java — layout ساده
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
        int bw = Math.min(280, this.width - 80);
        int bh = 24;
        int gap = 6;
        int cx = this.width / 2;

        int rows = 6;
        int innerH = rows * (bh + gap) + gap + 2 * (bh + gap) + 12;
        cardW = bw + 48;
        cardH = innerH + 90;
        cardX = cx - cardW / 2;
        cardY = Math.max(24, (this.height - cardH) / 2);

        int y = cardY + 74;
        int bx = cx - bw / 2;

        bHud   = new UiButton(1, bx, y,                       bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(40);
        bPart  = new UiButton(2, bx, y + 1 * (bh + gap),      bw, bh, "Menu particles").style(UiButton.TOGGLE).delay(70);
        bToast = new UiButton(3, bx, y + 2 * (bh + gap),      bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(100);
        bLoad  = new UiButton(4, bx, y + 3 * (bh + gap),      bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(130);
        bDisc  = new UiButton(8, bx, y + 4 * (bh + gap),      bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(160);
        bFade  = new UiButton(5, bx, y + 5 * (bh + gap),      bw, bh, "").delay(190);

        this.buttonList.add(bHud);
        this.buttonList.add(bPart);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bDisc);
        this.buttonList.add(bFade);

        int y2 = y + 6 * (bh + gap) + 12;
        this.buttonList.add(new UiButton(6, bx, y2,             bw, bh, "Minecraft Options...").icon(Draw.ICON_GEAR).delay(220));
        this.buttonList.add(new UiButton(7, bx, y2 + bh + gap,  bw, bh, "Done").style(UiButton.PRIMARY).icon(Draw.ICON_CHECK).delay(250));

        sync();
    }

    private void sync() {
        bHud.on = Settings.hud;
        bPart.on = false; // particles removed
        bToast.on = Settings.toasts;
        bLoad.on = Settings.customLoading;
        bDisc.on = Settings.discordRpc;
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: Settings.hud = !Settings.hud; break;
            case 2: /* particles removed — toggle no-op */ break;
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
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);

        Draw.panel(cardX, cardY, cardW, cardH, 10f, Theme.SURFACE, Theme.BORDER);

        float cx = this.width / 2f;
        Draw.centered("OPTIONS", cx, cardY + 26, Theme.TEXT, 1.8f, false);
        Draw.centered("KB Client preferences", cx, cardY + 50, Theme.MUTED, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
''')


# ===========================================================================
# 11) GuiAltManager.java — بدون shadow، ساده
# ===========================================================================
write(UI / "GuiAltManager.java", r'''package com.oryvex.kbclient.ui;

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
    private int statusColor = Theme.MUTED;
    private int cardX, cardY, cardW, cardH;
    private int cx, y, bw;

    public GuiAltManager(GuiScreen parent) {
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        Keyboard.enableRepeatEvents(true);
        bw = Math.min(240, this.width - 80);
        int bh = 24, gap = 6;
        cx = this.width / 2;
        y = this.height / 2 - 50;
        cardW = bw + 40;
        cardX = cx - cardW / 2;
        cardY = y - 40;
        cardH = 4 * (bh + gap) + 90;

        nameField = new GuiTextField(0, this.fontRendererObj, cx - bw / 2 + 8, y + 16, bw - 16, 14);
        nameField.setMaxStringLength(16);
        nameField.setFocused(true);
        nameField.setEnableBackgroundDrawing(false);
        nameField.setTextColor(Theme.TEXT);

        this.buttonList.add(new UiButton(1, cx - bw / 2, y + 50,             bw, bh, "Login (Offline)").style(UiButton.PRIMARY).delay(60));
        this.buttonList.add(new UiButton(2, cx - bw / 2, y + 50 + bh + gap,   bw, bh, "Generate Random Alt").delay(100));
        this.buttonList.add(new UiButton(3, cx - bw / 2, y + 50 + 2*(bh+gap), bw, bh, "Back").style(UiButton.DANGER).delay(140));
    }

    @Override
    public void onGuiClosed() { Keyboard.enableRepeatEvents(false); }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: login(nameField.getText()); break;
            case 2:
                String rnd = "KBAlt_" + (1000 + new java.util.Random().nextInt(9000));
                nameField.setText(rnd);
                login(rnd);
                break;
            case 3: closeTo(parent); break;
        }
    }

    private void login(String name) {
        if (name == null || name.trim().isEmpty()) {
            status = "Username cannot be empty!";
            statusColor = Theme.BAD;
            return;
        }
        try {
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
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);
        Draw.panel(cardX, cardY, cardW, cardH, 10f, Theme.SURFACE, Theme.BORDER);

        Draw.centered("ALT MANAGER", cx, cardY + 20, Theme.TEXT, 1.4f, false);
        Draw.centered("Current: " + this.mc.getSession().getUsername(), cx, cardY + 40, Theme.ACCENT, 0.85f, false);

        Draw.roundRect(cx - bw / 2f, y + 10, bw, 24, 5f, Theme.SURFACE2);
        Draw.roundOutline(cx - bw / 2f, y + 10, bw, 24, 5f, 1f,
                nameField.isFocused() ? Theme.ACCENT : Theme.BORDER);
        nameField.drawTextBox();

        Draw.centered(status, cx, cardY + cardH - 16, statusColor, 0.85f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
''')


# ===========================================================================
# 12) Hud.java — flat
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
        final String text; final int color; final long born;
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
        if (Settings.watermark) {
            Draw.right("Created by muvixo", res.getScaledWidth() - 6,
                    res.getScaledHeight() - 10, Theme.DIM, 0.7f, false);
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
        int h = goal ? 56 : 48;

        Draw.roundRect(x, y, w, h, 6f, Draw.fade(Theme.SURFACE, a));
        Draw.roundOutline(x, y, w, h, 6f, 1f, Draw.fade(Theme.BORDER, a));
        Draw.rect(x + 1, y + 1, 3, h - 2, Draw.fade(t.isRecording() ? Theme.ACCENT : Theme.MUTED, a));

        Draw.left("KB CLIENT", x + 10, y + 12, Draw.fade(Theme.TEXT, a), 0.85f, false);
        Draw.right(t.isRecording() ? "REC" : "PAUSED", x + w - 10, y + 12,
                Draw.fade(t.isRecording() ? Theme.GOOD : Theme.WARN, a), 0.8f, false);

        if (last != null) {
            Draw.left("H " + KBProfile.f(last.h, 4) + "   V " + KBProfile.f(last.vy, 4),
                    x + 10, y + 26, Draw.fade(Theme.SOFT, a), 0.9f, false);
        } else {
            Draw.left("Waiting for hits...", x + 10, y + 26, Draw.fade(Theme.MUTED, a), 0.9f, false);
        }
        Draw.left(pr.used + " / " + pr.total + " samples", x + 10, y + 38,
                Draw.fade(Theme.MUTED, a), 0.75f, false);

        if (goal) {
            Draw.bar(x + 10, y + h - 10, w - 20, 3,
                    t.getSessionHits() / (double) t.getGoal(),
                    Draw.fade(Theme.SURFACE3, a), Draw.fade(Theme.ACCENT, a));
        }

        long now = System.currentTimeMillis();
        for (int i = toasts.size() - 1; i >= 0; i--) {
            if (now - toasts.get(i).born > 3600) toasts.remove(i);
        }
        int ty = y + h + 6;
        for (int i = toasts.size() - 1; i >= 0; i--) {
            Toast to = toasts.get(i);
            long age = now - to.born;
            float in   = age < 160 ? age / 160f : 1f;
            float fade = (age > 2800 ? 1f - (age - 2800) / 800f : 1f) * in * a;
            int tw = Draw.width(to.text, 0.85f) + 16;
            Draw.roundRect(x, ty, tw, 16, 4f, Draw.alpha(Theme.SURFACE, 0.95f * fade));
            Draw.roundOutline(x, ty, tw, 16, 4f, 1f, Draw.alpha(Theme.BORDER, fade));
            int al = (int)(255 * fade);
            if (al > 4) Draw.left(to.text, x + 8, ty + 8, (al << 24) | (to.color & 0xFFFFFF), 0.85f, false);
            ty += 18;
        }
    }
}
''')


# ===========================================================================
# 13) LoadingArt.java — flat
# ===========================================================================
write(UI / "LoadingArt.java", r'''package com.oryvex.kbclient.ui;

public final class LoadingArt {
    private LoadingArt() {}

    private static final String[] TIPS = {
        "Press Right Shift in-game to open the Knockback Analyzer.",
        "Get hit by a walking AND a sprinting player to separate HORIZONTAL from EXTRA-HORIZONTAL.",
        "Get hit while falling to measure VERTICAL when Y-LIMIT clamps it.",
        "Use /kb import to compare a Carbon YAML against your detected profile."
    };

    public static void draw(int w, int h, String title, String sub, int pct) {
        Draw.rect(0, 0, w, h, Theme.BG0);

        int cx = w / 2;
        int cy = h / 2;

        // logo
        float scale = 3f;
        Draw.centered("ORYVEX", cx, cy - 70, Theme.TEXT, scale, false);
        Draw.centered("K N O C K B A C K   C L I E N T", cx,
                cy - 70 + Draw.lineH(scale) + 10, Theme.MUTED, 0.85f, false);

        // spinner (simple rotating dots)
        long t = System.currentTimeMillis();
        int sy = cy + 10;
        int dots = 8;
        for (int i = 0; i < dots; i++) {
            double ang = (t / 300.0) + (Math.PI * 2 * i) / dots;
            int dx = (int)Math.round(Math.cos(ang) * 14);
            int dy = (int)Math.round(Math.sin(ang) * 14);
            float fa = 0.25f + 0.75f * (i / (float)dots);
            Draw.circle(cx + dx, sy + dy, 2f, Draw.alpha(Theme.ACCENT, fa));
        }

        // text
        String ttl = (title == null || title.isEmpty()) ? "Loading" : title;
        Draw.centered(ttl, cx, cy + 44, Theme.TEXT, 1.0f, false);
        if (sub != null && !sub.isEmpty()) {
            Draw.centered(sub, cx, cy + 44 + Draw.lineH(1.0f) + 6, Theme.MUTED, 0.85f, false);
        }

        // progress bar
        int bw = 200, bx = cx - bw / 2, by = cy + 78;
        Draw.roundRect(bx, by, bw, 4, 2, Theme.SURFACE3);
        if (pct >= 0) {
            int fw = Math.max(2, bw * Math.min(100, pct) / 100);
            Draw.roundRect(bx, by, fw, 4, 2, Theme.ACCENT);
            Draw.centered(pct + "%", cx, by + 14, Theme.MUTED, 0.8f, false);
        } else {
            // indeterminate
            double p = (t % 1600L) / 1600.0;
            int seg = 60;
            int sx = bx + (int)((bw + seg) * p) - seg;
            int x0 = Math.max(bx, sx);
            int x1 = Math.min(bx + bw, sx + seg);
            if (x1 > x0) Draw.roundRect(x0, by, x1 - x0, 4, 2, Theme.ACCENT);
        }

        // tip
        String tip = "TIP  " + TIPS[(int)((System.currentTimeMillis() / 4500L) % TIPS.length)];
        Draw.centered(tip, cx, h - 24, Theme.DIM, 0.85f, false);
        Draw.left("KB Client 3.0", 8, h - 10, Theme.DIM, 0.75f, false);
    }
}
''')


# ===========================================================================
# 14) KBClientMod — مطمئن شو UiButton.ICON_GEAR کار می‌کنه
#     (alias اضافه شده در UiButton)
# ===========================================================================
MOD = JAVA / "KBClientMod.java"
if MOD.exists():
    t = MOD.read_text(encoding="utf-8")
    if "UiButton.ICON_GEAR" in t:
        print(f"  [ OK  ] KBClientMod uses UiButton.ICON_GEAR (alias provided)")


print()
print("Done. Rebuild:  ./gradlew clean build")
print("همه shader/glow/shadow/radial/particle حذف شدن.")