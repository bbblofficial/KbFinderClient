#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adder.py - full cleanup for KB Client

* Draw.java          -> rewritten from scratch, no icons, guaranteed to compile
* UiButton.java      -> flat, no icon code at all
* GuiModernMenu.java -> no icon(...) calls
* GuiKbOptions.java  -> no icon(...) calls
* TransparentOverlays-> scoreboard + tab list, no backgrounds
* KBClientMod.java   -> stop replacing mc.fontRendererObj (fixes the ▏ glyphs)

Run from the project root (where build.gradle is):
    python adder.py
"""

import os, sys, shutil, datetime

ROOT  = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(ROOT, "src", "main", "java", "com", "oryvex", "kbclient")
UI    = os.path.join(SRC, "ui")
STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p):
    if os.path.isfile(p):
        shutil.copy2(p, p + ".bak_" + STAMP)


def write(p, content):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    backup(p)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    print("  write ", os.path.relpath(p, ROOT))


def patch(path, pairs):
    if not os.path.isfile(path):
        print("  miss  ", os.path.relpath(path, ROOT)); return
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    orig = txt
    for old, new in pairs:
        if old not in txt:
            print("  warn  ", "pattern not found in", os.path.basename(path))
            continue
        txt = txt.replace(old, new, 1)
    if txt != orig:
        backup(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt)
        print("  patch ", os.path.relpath(path, ROOT))


# =====================================================================
#  Draw.java  -  clean, no icons, no unused code
# =====================================================================
DRAW = r'''package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;

import java.util.ArrayList;
import java.util.List;

/** Minimal drawing toolkit. Icons have been removed entirely. */
public final class Draw {
    private Draw() {}

    /* ---- icon IDs (kept only so old source still compiles) ---- */
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

    /* ================== math helpers ================== */
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

    public static float lerp(float a, float b, float t) {
        return a + (b - a) * clamp(t);
    }

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

    /* ================== GL state ================== */
    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void resetColor() {
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.disableBlend();
    }

    /* ================== primitives ================== */
    public static void rect(float x, float y, float w, float h, int color) {
        Gui.drawRect((int) x, (int) y, (int)(x + w), (int)(y + h), color);
    }

    public static void vgradient(int w, int h, int top, int bottom) {
        rect(0, 0, w, h, top);
    }

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

    public static void line(float x1, float y1, float x2, float y2,
                            float width, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        float dx = x2 - x1, dy = y2 - y1;
        float len = (float) Math.sqrt(dx * dx + dy * dy);
        if (len < 0.01f) return;
        int steps = (int) Math.ceil(len);
        for (int i = 0; i <= steps; i++) {
            float t = i / (float) steps;
            rect(x1 + dx * t - width / 2f, y1 + dy * t - width / 2f,
                 width, width, color);
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

    /* ================== icons: NO-OP ================== */
    /** Kept so existing call sites still compile - draws nothing. */
    public static void icon(int type, float cx, float cy, float size, int color) {
        /* icons removed from the design */
    }

    /* ================== text ================== */
    public static FontRenderer font() {
        try {
            com.oryvex.kbclient.font.ModernFontRenderer mf =
                    com.oryvex.kbclient.KBClientMod.modernFont;
            if (mf != null) return mf;
        } catch (Throwable ignored) { }
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

    public static void text(String s, float x, float y,
                            int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, false);
        GlStateManager.popMatrix();
    }

    public static void centered(String s, float cx, float cy,
                                int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, cx - tw / 2f, cy - th / 2f, color, scale, false);
    }

    public static void mid(String s, float cx, float cy,
                           int color, float scale, boolean shadow) {
        centered(s, cx, cy, color, scale, false);
    }

    public static void mid(String s, float cx, float cy,
                           int color, float scale) {
        centered(s, cx, cy, color, scale, false);
    }

    public static void left(String s, float x, float cy,
                            int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float th = font().FONT_HEIGHT * scale;
        text(s, x, cy - th / 2f, color, scale, false);
    }

    public static void right(String s, float rx, float cy,
                             int color, float scale, boolean shadow) {
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
'''


# =====================================================================
#  UiButton.java  -  no icons at all
# =====================================================================
UIBUTTON = r'''package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;

/** Flat, minimal button. No icons anywhere. */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public static final int GHOST   = 5;

    /* compatibility aliases - they draw nothing */
    public static final int ICON_NONE = 0;
    public static final int ICON_GEAR = 0;

    public int style = NORMAL;
    public int icon  = 0;          /* kept only for source compatibility */
    public boolean selected;
    public boolean on;
    public long delay;
    public boolean left;
    public float textSize = 1f;

    private final Anim hover = new Anim();
    private final long born = System.currentTimeMillis();

    public UiButton(int id, int x, int y, int w, int h, String text) {
        super(id, x, y, w, h, text);
    }

    public UiButton style(int s)  { this.style = s; return this; }
    public UiButton icon(int i)   { return this; }   /* no-op */
    public UiButton delay(long d) { this.delay = d; return this; }
    public UiButton left()        { this.left = true; return this; }
    public UiButton size(float s) { this.textSize = s; return this; }

    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= xPosition && mouseY >= yPosition
                && mouseX < xPosition + width && mouseY < yPosition + height;

        float hv = hover.to((hovered && enabled) ? 1f : 0f, 24f);
        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 220f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.55f;

        float x  = xPosition;
        float y  = yPosition + (1f - ap) * 4f;
        float w  = width;
        float h  = height;
        float r  = 4f;
        float cy = y + h / 2f;

        int bg, border, txt;
        switch (style) {
            case PRIMARY:
                bg     = Draw.lerp(Theme.ACCENT_DK, Theme.ACCENT, hv);
                border = Theme.ACCENT;
                txt    = 0xFFFFFFFF;
                break;
            case DANGER:
                bg     = Draw.lerp(0x18FB7185, 0x55FB7185, hv);
                border = Draw.lerp(0x44FB7185, Theme.BAD, hv);
                txt    = Draw.lerp(0xFFFCA5A5, 0xFFFFFFFF, hv);
                break;
            case TAB:
                bg     = selected ? Theme.SURFACE2 : Draw.lerp(0x00000000, Theme.SURFACE2, hv);
                border = selected ? Theme.BORDER_HI : Theme.BORDER;
                txt    = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            case TOGGLE:
                bg     = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv);
                border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv);
                txt    = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
                break;
            case GHOST:
                bg     = Draw.lerp(0x00000000, Theme.SURFACE2, hv);
                border = 0;
                txt    = Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            default:
                bg     = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv);
                border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv);
                txt    = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
        }
        bg     = Draw.fade(bg,     ap);
        border = Draw.fade(border, ap);
        txt    = Draw.fade(txt,    ap);

        Draw.roundRect(x, y, w, h, r, bg);
        if (((border >>> 24) & 255) > 4)
            Draw.roundOutline(x, y, w, h, r, 1f, border);

        if (style == TOGGLE) {
            float sw = 22f, sh = 12f;
            float sx = x + w - sw - 10f;
            Draw.left(Draw.fit(displayString, w - sw - 26f, textSize, false),
                      x + 12f, cy, txt, textSize, false);
            drawToggle(sx, cy - sh / 2f, sw, sh, on ? 1f : 0f, ap);
            return;
        }

        String label = Draw.fit(displayString, w - 20f, textSize, false);
        float tw = Draw.w(label, textSize, false);
        float startX = left ? x + 12f : x + (w - tw) / 2f;
        Draw.left(label, startX, cy, txt, textSize, false);

        if (style == TAB && selected) {
            Draw.rect(x + 8f, y + h - 2f, w - 16f, 2f, Theme.ACCENT);
        }
    }

    private void drawToggle(float sx, float sy, float sw, float sh,
                            float knob, float ap) {
        int track = on ? Theme.ACCENT : 0x30FFFFFF;
        Draw.roundRect(sx, sy, sw, sh, sh / 2f, Draw.fade(track, ap));
        float kx = sx + sh / 2f + (sw - sh) * knob;
        Draw.circle(kx, sy + sh / 2f, sh / 2f - 1.5f, Draw.fade(0xFFFFFFFF, ap));
    }
}
'''


# =====================================================================
#  GuiModernMenu.java  -  no icon() calls
# =====================================================================
GUI_MODERN_MENU = r'''package com.oryvex.kbclient.ui;

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

    public GuiModernMenu(KBTracker tracker) { this.tracker = tracker; }

    @Override
    public void initGui() {
        this.buttonList.clear();
        sidebarW = Math.max(200, Math.min(320, (int)(this.width * 0.30f)));

        int pad = 22;
        int bw  = sidebarW - pad * 2;
        int bh  = 26;
        int gap = 8;
        int totalH = 6 * bh + 5 * gap;
        int top = Math.max(110, (this.height - totalH) / 2 + 16);

        buttonList.add(new UiButton(1, pad, top,                bw, bh, "Singleplayer").delay(40));
        buttonList.add(new UiButton(2, pad, top + 1*(bh+gap),   bw, bh, "Multiplayer").delay(70));
        buttonList.add(new UiButton(6, pad, top + 2*(bh+gap),   bw, bh, "Alt Manager").delay(100));
        buttonList.add(new UiButton(3, pad, top + 3*(bh+gap),   bw, bh, "Analyzer")
                .style(UiButton.PRIMARY).delay(130));
        buttonList.add(new UiButton(4, pad, top + 4*(bh+gap),   bw, bh, "Options").delay(160));
        buttonList.add(new UiButton(5, pad, top + 5*(bh+gap),   bw, bh, "Quit")
                .style(UiButton.DANGER).delay(190));
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
    protected void onKey(char c, int key) { }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);
        Draw.rect(0, 0, sidebarW, this.height, Theme.SURFACE);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        float tScale = Math.max(1.5f, Math.min(2.2f, sidebarW / 140f));
        Draw.centered("ORYVEX", sidebarW / 2f, 52f, Theme.TEXT, tScale, false);

        float sScale = 0.85f;
        Draw.centered("KB Client v" + KBClientMod.VERSION, sidebarW / 2f,
                      52f + Draw.lineH(tScale) + 6f, Theme.MUTED, sScale, false);

        float divY = 52f + Draw.lineH(tScale) + Draw.lineH(sScale) + 16f;
        Draw.rect(sidebarW * 0.2f, divY, sidebarW * 0.6f, 1f, Theme.BORDER);

        KBProfile p = tracker.getProfile();
        if (p.hasData && this.width > sidebarW + 160) {
            String s = p.summary();
            int w = Draw.width(s, 0.85f) + 46;
            int px = this.width - w - 18;
            int py = 18;
            Draw.roundRect(px, py, w, 26, 6f, Theme.SURFACE2);
            Draw.roundOutline(px, py, w, 26, 6f, 1f, Theme.BORDER);
            Draw.circle(px + 14, py + 13, 4f, Theme.GOOD);
            Draw.left("Profile", px + 26, py + 8,  Theme.MUTED, 0.72f, false);
            Draw.left(s,         px + 26, py + 18, Theme.TEXT,  0.85f, false);
        }

        int userY = this.height - 34;
        Draw.rect(sidebarW * 0.2f, userY - 18, sidebarW * 0.6f, 1f, Theme.BORDER);
        int avX = 22, avY = userY - 8;
        Draw.roundRect(avX, avY, 22, 22, 11f, Theme.SURFACE3);
        Draw.circle(avX + 11f, avY + 11f, 6f, Theme.SOFT);

        Draw.left("Logged in as", 52, userY - 2, Theme.MUTED, 0.72f, false);
        String name = mc.getSession().getUsername();
        Draw.left(Draw.fit(name, sidebarW - 70, 0.9f, false),
                  52, userY + 8, Theme.TEXT, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
'''


# =====================================================================
#  GuiKbOptions.java  -  no icons
# =====================================================================
GUI_KB_OPTIONS = r'''package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiOptions;
import net.minecraft.client.gui.GuiScreen;

public class GuiKbOptions extends FadeScreen {
    private final KBTracker tracker;
    private final GuiScreen parent;

    private UiButton bHud, bToast, bLoad, bDisc, bFade;

    private int cardX, cardY, cardW, cardH;

    public GuiKbOptions(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent  = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();

        int cx = this.width / 2;
        int bw = Math.min(300, this.width - 80);
        int bh = 22;
        int gap = 5;

        int pad = 24, headerH = 88;
        int togglesH = 5 * (bh + gap) - gap;
        int actionsGap = 12, actionsH = bh, footerH = 40;

        cardW = bw + pad * 2;
        cardH = pad + headerH + togglesH + actionsGap + actionsH + footerH + pad;
        cardX = cx - cardW / 2;
        cardY = Math.max(16, (this.height - cardH) / 2);

        int togglesY = cardY + pad + headerH;
        int bx = cx - bw / 2;

        bHud   = new UiButton(1, bx, togglesY,                bw, bh, "HUD overlay")
                .style(UiButton.TOGGLE).delay(50);
        bToast = new UiButton(3, bx, togglesY + 1*(bh+gap),   bw, bh, "Hit toasts")
                .style(UiButton.TOGGLE).delay(90);
        bLoad  = new UiButton(4, bx, togglesY + 2*(bh+gap),   bw, bh, "Custom loading screen")
                .style(UiButton.TOGGLE).delay(130);
        bDisc  = new UiButton(8, bx, togglesY + 3*(bh+gap),   bw, bh, "Discord Rich Presence")
                .style(UiButton.TOGGLE).delay(170);
        bFade  = new UiButton(5, bx, togglesY + 4*(bh+gap),   bw, bh, "").delay(210);

        buttonList.add(bHud);
        buttonList.add(bToast);
        buttonList.add(bLoad);
        buttonList.add(bDisc);
        buttonList.add(bFade);

        int actionY = togglesY + togglesH + actionsGap;
        int ag    = 8;
        int halfW = (bw - ag) / 2;

        UiButton mcOpt = new UiButton(6, bx, actionY, halfW, bh, "MC Options").delay(250);
        UiButton done  = new UiButton(7, bx + halfW + ag, actionY, halfW, bh, "Done")
                .style(UiButton.PRIMARY).delay(290);

        buttonList.add(mcOpt);
        buttonList.add(done);

        sync();
    }

    private void sync() {
        bHud.on   = Settings.hud;
        bToast.on = Settings.toasts;
        bLoad.on  = Settings.customLoading;
        bDisc.on  = Settings.discordRpc;
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: Settings.hud           = !Settings.hud;           break;
            case 3: Settings.toasts        = !Settings.toasts;        break;
            case 4: Settings.customLoading = !Settings.customLoading; break;
            case 8:
                Settings.discordRpc = !Settings.discordRpc;
                com.oryvex.kbclient.DiscordRPC.apply();
                break;
            case 5: Settings.fade = (Settings.fade + 1) % 4;          break;
            case 6: closeTo(new GuiOptions(this, this.mc.gameSettings)); return;
            case 7: Settings.save(); closeTo(parent);                    return;
            default: break;
        }
        Settings.save();
        sync();
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        if (key == org.lwjgl.input.Keyboard.KEY_ESCAPE) {
            Settings.save();
            closeTo(parent);
        }
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);
        Draw.panel(cardX, cardY, cardW, cardH, 8f, Theme.SURFACE, Theme.BORDER);

        float cx = this.width / 2f;
        float titleCY = cardY + 44f;
        Draw.centered("OPTIONS",               cx, titleCY,       Theme.TEXT,  1.8f,  false);
        Draw.centered("KB Client preferences", cx, titleCY + 24f, Theme.MUTED, 0.85f, false);
        Draw.rect(cx - 30f, titleCY + 42f, 60f, 1f, Theme.BORDER);

        Draw.centered("KB Client 3.0  |  Forge 1.8.9",
                      cx, cardY + cardH - 20f, Theme.DIM, 0.7f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
'''


# =====================================================================
#  TransparentOverlays.java  -  scoreboard + tab only
# =====================================================================
TRANSPARENT = r'''package com.oryvex.kbclient;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiIngame;
import net.minecraft.client.gui.ScaledResolution;
import net.minecraft.scoreboard.Score;
import net.minecraft.scoreboard.ScoreObjective;
import net.minecraft.scoreboard.ScorePlayerTeam;
import net.minecraft.scoreboard.Scoreboard;
import net.minecraft.scoreboard.Team;
import net.minecraft.util.EnumChatFormatting;

import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

/**
 * Draws the scoreboard sidebar and the tab list WITHOUT any background panel.
 * The text / colours / positions are identical to vanilla - only the dark
 * rectangles behind them are removed.
 *
 * Chat is intentionally not touched: GuiNewChat.drawChat is not a portable
 * override on 1.8.9 (its `mc` field is private) and messing with it via
 * reflection produces more harm than good.
 */
public final class TransparentOverlays {
    private TransparentOverlays() {}

    private static boolean installed;

    public static void install() {
        if (installed) return;
        installed = true;
        try {
            Minecraft mc = Minecraft.getMinecraft();
            GuiIngame vanilla = mc.ingameGUI;
            if (vanilla == null) return;

            GuiIngame replacement = new TransparentGuiIngame(mc);
            ObfuscationReflectionHelper.setPrivateValue(
                    Minecraft.class, mc, replacement,
                    "ingameGUI", "field_71456_v");

            MinecraftForge.EVENT_BUS.register(new TabHider());
            KBClientMod.logger.info("[KBClient] transparent overlays installed");
        } catch (Throwable t) {
            KBClientMod.logger.error("[KBClient] TransparentOverlays failed: " + t);
        }
    }

    public static class TransparentGuiIngame extends GuiIngame {
        private final Minecraft mcRef;

        public TransparentGuiIngame(Minecraft mc) {
            super(mc);
            this.mcRef = mc;
        }

        @Override
        protected void renderScoreboard(ScoreObjective objective, ScaledResolution sr) {
            if (objective == null) return;

            Scoreboard sb = objective.getScoreboard();
            Collection<Score> all = sb.getSortedScores(objective);

            List<Score> list = new ArrayList<Score>();
            for (Score s : all) {
                String n = s.getPlayerName();
                if (n != null && !n.startsWith("#")) list.add(s);
            }
            if (list.size() > 15) {
                list = new ArrayList<Score>(list.subList(list.size() - 15, list.size()));
            }
            if (list.isEmpty()) return;

            int w = this.mcRef.fontRendererObj.getStringWidth(
                    objective.getDisplayName().getFormattedText());
            for (Score s : list) {
                Team t = sb.getPlayersTeam(s.getPlayerName());
                String line = ScorePlayerTeam.formatPlayerName(t, s.getPlayerName())
                            + EnumChatFormatting.RED + s.getScorePoints();
                w = Math.max(w, this.mcRef.fontRendererObj.getStringWidth(line));
            }

            int lineH  = this.mcRef.fontRendererObj.FONT_HEIGHT;
            int totalH = list.size() * lineH;
            int y0     = sr.getScaledHeight() / 2 + totalH / 3;
            int right  = sr.getScaledWidth() - 3;
            int left   = right - w;
            int xRight = right + 2;

            int j = 0;
            for (Score s : list) {
                ++j;
                Team t = sb.getPlayersTeam(s.getPlayerName());
                String name = ScorePlayerTeam.formatPlayerName(t, s.getPlayerName());
                String pts  = EnumChatFormatting.RED + "" + s.getScorePoints();
                int y = y0 - j * lineH;

                /* >>> no dark background rects - that is the whole point <<< */
                this.mcRef.fontRendererObj.drawString(name, left, y, 553648127);
                this.mcRef.fontRendererObj.drawString(
                        pts,
                        xRight - this.mcRef.fontRendererObj.getStringWidth(pts),
                        y, 553648127);

                if (j == list.size()) {
                    String title = objective.getDisplayName().getFormattedText();
                    this.mcRef.fontRendererObj.drawString(
                            title,
                            left + w / 2
                                    - this.mcRef.fontRendererObj.getStringWidth(title) / 2,
                            y - lineH, 553648127);
                }
            }
        }
    }

    public static class TabHider {
        @SubscribeEvent
        public void onRenderPre(RenderGameOverlayEvent.Pre e) {
            if (e.type == RenderGameOverlayEvent.ElementType.PLAYER_LIST) {
                e.setCanceled(true);
            }
        }
    }
}
'''


# =====================================================================
#  main
# =====================================================================
def main():
    print("== KB Client - full cleanup ==")
    if not os.path.isdir(SRC):
        print("!! Run this from the project root (where build.gradle is).")
        sys.exit(1)

    print("\n[1/6] Draw.java (clean, no icons)")
    write(os.path.join(UI, "Draw.java"), DRAW)

    print("\n[2/6] UiButton.java (no icons)")
    write(os.path.join(UI, "UiButton.java"), UIBUTTON)

    print("\n[3/6] GuiModernMenu.java (no icon calls)")
    write(os.path.join(UI, "GuiModernMenu.java"), GUI_MODERN_MENU)

    print("\n[4/6] GuiKbOptions.java (no icon calls)")
    write(os.path.join(UI, "GuiKbOptions.java"), GUI_KB_OPTIONS)

    print("\n[5/6] TransparentOverlays.java (scoreboard + tab)")
    write(os.path.join(SRC, "TransparentOverlays.java"), TRANSPARENT)

    print("\n[6/6] KBClientMod.java (do not replace mc.fontRendererObj)")
    kbmod = os.path.join(SRC, "KBClientMod.java")
    patch(kbmod, [
        # Stop swapping the vanilla font - that's what broke the ▏ glyphs.
        (
            "mcF.fontRendererObj = modernFont;",
            "// mcF.fontRendererObj NOT replaced - only Draw.font() uses modernFont"
        ),
        # Install transparent overlays
        (
            "installLoading();\n            if (Settings.discordRpc) DiscordRPC.start();",
            "installLoading();\n"
            "            com.oryvex.kbclient.TransparentOverlays.install();\n"
            "            if (Settings.discordRpc) DiscordRPC.start();"
        ),
        (
            "installLoading();\n            DiscordRPC.start();",
            "installLoading();\n"
            "            com.oryvex.kbclient.TransparentOverlays.install();\n"
            "            DiscordRPC.start();"
        ),
        (
            "installLoading();\n            try {\n"
            "                Minecraft mcF = Minecraft.getMinecraft();",
            "installLoading();\n"
            "            com.oryvex.kbclient.TransparentOverlays.install();\n"
            "            try {\n"
            "                Minecraft mcF = Minecraft.getMinecraft();"
        ),
    ])

    print("\n== done ==")
    print("Rebuild with:  ./gradlew build")


if __name__ == "__main__":
    main()