#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fixer_v4.py — بازطراحی کامل دکمه و UI
- آیکون درست اندازه (radius = size/2)
- دکمه با طراحی جدید مدرن
- Layout بهتر و فاصله‌گذاری درست
- آیکون‌های برداری تمیز برای gear, arrow, plus, minus, copy, save, close, check
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
# 1) Draw.java — بازنویسی کامل با آیکون‌های برداری درست
# ===========================================================================
write(UI / "Draw.java", r'''package com.oryvex.kbclient.ui;

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
}
''')


# ===========================================================================
# 2) UiButton.java — بازطراحی کامل با اندازه‌گذاری درست آیکون
# ===========================================================================
write(UI / "UiButton.java", r'''package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import org.lwjgl.input.Mouse;

/**
 * Modern flat button with:
 *  - Correct icon sizing (never exceeds button height)
 *  - Smooth hover / press / toggle animations
 *  - Staggered intro animation
 *  - Multiple styles: NORMAL, PRIMARY, DANGER, TAB, TOGGLE, GHOST
 */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public static final int GHOST   = 5;

    public int style = NORMAL;
    public int icon = Draw.ICON_NONE;
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

        // press feedback: shift down 1px and reduce height 1px
        float x = xPosition + pr * 0.5f;
        float y = yPosition + pr * 0.5f + (1f - ap) * 8f;
        float w = width - pr;
        float h = height - pr;
        float r = Math.min(h / 2f, style == TAB ? 4f : 6f);
        float cy = y + h / 2f;

        int accent  = Theme.accent();
        int accent2 = Theme.accent2();
        int textCol;

        switch (style) {
            case PRIMARY: {
                int c1 = Draw.lerp(Draw.shade(accent, 0.75f), accent, hv);
                int c2 = Draw.lerp(Draw.shade(accent2, 0.75f), accent2, hv);
                Draw.roundRect(x, y, w, h, r, Draw.fade(c1, ap));
                Draw.roundRect(x, y + h * 0.4f, w, h * 0.6f, r, Draw.fade(c2, ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(0x33FFFFFF, ap));
                textCol = 0xFFFFFFFF;
                break;
            }
            case DANGER: {
                int fill = Draw.lerp(0x22FB7185, 0x55FB7185, hv);
                Draw.roundRect(x, y, w, h, r, Draw.fade(fill, ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(0x44FB7185, 0xFFFB7185, hv), ap));
                textCol = Draw.lerp(0xFFFCA5A5, 0xFFFFFFFF, hv);
                break;
            }
            case TAB: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(selected ? Theme.FILL_HI : Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            case TOGGLE: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv * 0.7f), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.5f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, Math.max(hv, kn * 0.5f));
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
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.65f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
            }
        }

        textCol = Draw.fade(textCol, ap);

        if (style == TOGGLE) {
            // label on left, switch on right
            float sw = 22f, sh = 12f;
            float sx = x + w - sw - 10f;
            Draw.left(Draw.fit(displayString, w - sw - 26f, textSize, false),
                    x + 10f, cy, textCol, textSize, false);
            drawToggleSwitch(sx, cy - sh / 2f, sw, sh, kn, ap);
            return;
        }

        // ---- icon sizing: icon diameter = min(button height * 0.55, 12) ----
        boolean hasIcon = icon != Draw.ICON_NONE;
        float iconSize = Math.min(h * 0.55f, 12f);
        float gap = 6f;

        String label = Draw.fit(displayString,
                w - (hasIcon ? iconSize + gap + 20f : 20f), textSize, false);
        float tw = Draw.w(label, textSize, false);

        float contentW = hasIcon ? iconSize + gap + tw : tw;
        float startX;
        if (left) startX = x + 12f;
        else      startX = x + (w - contentW) / 2f;

        if (hasIcon) {
            float icx = startX + iconSize / 2f;
            int ic = (style == PRIMARY) ? textCol
                    : Draw.fade(Draw.lerp(Theme.SOFT, accent, hv), ap);
            if (style == DANGER) ic = textCol;
            Draw.icon(icon, icx, cy, iconSize, ic);
            startX += iconSize + gap;
        }

        if (left) {
            Draw.left(label, startX, cy, textCol, textSize, style == PRIMARY);
        } else {
            Draw.left(label, startX, cy, textCol, textSize, style == PRIMARY);
        }

        if (style == TAB && selected) {
            Draw.roundRect(x + 8f, y + h - 2f, w - 16f, 2f, 1f, Draw.fade(accent, ap));
        }
    }

    private void drawToggleSwitch(float sx, float sy, float sw, float sh, float knob, float ap) {
        int off = Draw.fade(0x30FFFFFF, ap);
        int onC = Draw.fade(Theme.accent(), ap);
        int track = Draw.lerp(off, onC, knob);
        Draw.roundRect(sx, sy, sw, sh, sh / 2f, track);
        float kx = sx + sh / 2f + (sw - sh) * knob;
        Draw.circle(kx, sy + sh / 2f, sh / 2f - 1.5f, Draw.fade(0xFFFFFFFF, ap));
    }
}
''')


# ===========================================================================
# 3) GuiModernMenu — Layout جدید و تمیزتر
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

        // responsive sidebar: ~30% width, min 200, max 320
        sidebarW = Math.max(200, Math.min(320, (int)(this.width * 0.30f)));

        int padding = 24;
        int bw = sidebarW - padding * 2;
        int bh = 26;
        int gap = 8;

        int totalH = 6 * bh + 5 * gap;
        int top = Math.max(110, (this.height - totalH) / 2 + 20);

        this.buttonList.add(new UiButton(1, padding, top,                       bw, bh, "Singleplayer").icon(Draw.ICON_PLAY).delay(60));
        this.buttonList.add(new UiButton(2, padding, top + 1 * (bh + gap),      bw, bh, "Multiplayer").icon(Draw.ICON_GRAPH).delay(100));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap),      bw, bh, "Alt Manager").icon(Draw.ICON_USER).delay(140));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap),      bw, bh, "Analyzer").style(UiButton.PRIMARY).icon(Draw.ICON_GEAR).delay(180));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap),      bw, bh, "Options").icon(Draw.ICON_GEAR).delay(220));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap),      bw, bh, "Quit").style(UiButton.DANGER).icon(Draw.ICON_CLOSE).delay(260));
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
        // main menu cannot be closed with ESC
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);

        // ambient particles
        if (Settings.particles && Settings.density > 0) {
            Draw.plexusBackground(this.width, this.height, 0.35f);
        }

        // sidebar panel
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // ---- Title ----
        float titleScale = Math.max(1.6f, Math.min(2.4f, sidebarW / 130f));
        Draw.centered("ORYVEX", sidebarW / 2f, 55f, Theme.TEXT, titleScale, true);

        float subScale = 0.9f;
        float subY = 55f + Draw.lineH(titleScale) + 8f;
        Draw.centered("KB Client v" + KBClientMod.VERSION, sidebarW / 2f, subY, Theme.ACCENT, subScale, false);

        // divider
        int divY = (int)(subY + Draw.lineH(subScale) + 12f);
        Draw.rect(40, divY, sidebarW - 80, 1, Theme.BORDER);

        // ---- Profile chip (top-right) ----
        KBProfile p = tracker.getProfile();
        if (p.hasData && this.width > sidebarW + 160) {
            String s = p.summary();
            int w = Draw.width(s, 0.85f) + 48;
            int px = this.width - w - 18;
            int py = 18;
            Draw.roundRect(px, py, w, 26, 6f, Theme.PANEL2);
            Draw.roundOutline(px, py, w, 26, 6f, 1f, Theme.BORDER);
            Draw.circle(px + 14, py + 13, 4f, Theme.GOOD);
            Draw.left("Profile", px + 26, py + 8, Theme.MUTED, 0.7f, false);
            Draw.left(s,       px + 26, py + 18, Theme.TEXT, 0.85f, false);
        }

        // ---- User card (bottom-left) ----
        int userY = this.height - 36;
        Draw.rect(40, userY - 18, sidebarW - 80, 1, Theme.BORDER);

        // avatar circle
        int avX = 34, avY = userY - 8;
        Draw.roundRect(avX, avY, 22, 22, 11f, Theme.PANEL3);
        Draw.icon(Draw.ICON_USER, avX + 11f, avY + 11f, 12f, Theme.SOFT);

        Draw.left("Logged in as", 64, userY - 2, Theme.MUTED, 0.72f, false);
        String name = mc.getSession().getUsername();
        String nameF = Draw.fit(name, sidebarW - 80, 0.9f, false);
        Draw.left(nameF, 64, userY + 8, Theme.TEXT, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
''')


# ===========================================================================
# 4) GuiKbOptions — Layout جدید
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

        bHud   = new UiButton(1, bx, y,                          bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(60);
        bPart  = new UiButton(2, bx, y + 1 * (bh + gap),         bw, bh, "Menu particles").style(UiButton.TOGGLE).delay(100);
        bToast = new UiButton(3, bx, y + 2 * (bh + gap),         bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(140);
        bLoad  = new UiButton(4, bx, y + 3 * (bh + gap),         bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(180);
        bDisc  = new UiButton(8, bx, y + 4 * (bh + gap),         bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(220);
        bFade  = new UiButton(5, bx, y + 5 * (bh + gap),         bw, bh, "").delay(260);

        this.buttonList.add(bHud);
        this.buttonList.add(bPart);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bDisc);
        this.buttonList.add(bFade);

        int y2 = y + 6 * (bh + gap) + 12;
        this.buttonList.add(new UiButton(6, bx, y2,                 bw, bh, "Minecraft Options...").icon(Draw.ICON_GEAR).delay(300));
        this.buttonList.add(new UiButton(7, bx, y2 + bh + gap,      bw, bh, "Done").style(UiButton.PRIMARY).icon(Draw.ICON_CHECK).delay(340));

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
        Draw.panel(cardX, cardY, cardW, cardH, 10, Theme.GLASS, Theme.BORDER);

        float cx = this.width / 2f;
        Draw.centered("OPTIONS", cx, cardY + 26, Theme.TEXT, 1.8f, true);
        Draw.centered("KB Client preferences", cx, cardY + 50, Theme.MUTED, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
''')


# ===========================================================================
# 5) Ui.java — toggle switch بازطراحی
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
        float w = 22f, h = 12f, y = cy - h / 2f;
        int off = Draw.fade(0x30FFFFFF, alpha);
        int onC = Draw.fade(Theme.accent(), alpha);
        int track = Draw.lerp(off, onC, knob);
        Draw.roundRect(x, y, w, h, h / 2f, track);
        float kx = x + h / 2f + (w - h) * knob;
        Draw.circle(kx, cy, h / 2f - 1.5f, Draw.fade(0xFFFFFFFF, alpha));
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


print()
print("Done. Rebuild:  .\\gradlew clean build")