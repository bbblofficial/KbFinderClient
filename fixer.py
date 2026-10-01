#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adder.py
========
Applies the "simpler design + transparent overlays + better toasts" patch
to the KB Client (Minecraft 1.8.9 Forge) source tree.

Run this from the project root (where build.gradle and src/ live):
    python adder.py
"""

import os
import sys
import shutil
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src", "main", "java", "com", "oryvex", "kbclient")
UI   = os.path.join(SRC, "ui")

STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(path):
    if os.path.isfile(path):
        shutil.copy2(path, path + ".bak_" + STAMP)


def write(path, content, overwrite=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.isfile(path) and not overwrite:
        print("  skip  ", os.path.relpath(path, ROOT))
        return
    backup(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  write ", os.path.relpath(path, ROOT))


def patch(path, pairs):
    """pairs = list of (old, new).  Replaces each old once."""
    if not os.path.isfile(path):
        print("  miss  ", os.path.relpath(path, ROOT)); return False
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
        return True
    return False


# =====================================================================
#  1.  SIMPLER UiButton.java  (no icons, no gear)
# =====================================================================
UIBUTTON = r'''package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;

/** Flat, minimal button.  No icons, no glow. */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public static final int GHOST   = 5;

    /* legacy names kept so older callers still compile */
    public static final int ICON_NONE = 0;
    public static final int ICON_GEAR = 0;

    public int style = NORMAL;
    public int icon  = 0;
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

    public UiButton style(int s)   { this.style = s; return this; }
    public UiButton icon(int i)    { return this; }          /* no-op */
    public UiButton delay(long d)  { this.delay = d; return this; }
    public UiButton left()         { this.left = true; return this; }
    public UiButton size(float s)  { this.textSize = s; return this; }

    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= xPosition && mouseY >= yPosition
                && mouseX < xPosition + width && mouseY < yPosition + height;

        float hv = hover.to((hovered && enabled) ? 1f : 0f, 24f);
        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 240f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.55f;

        float x = xPosition;
        float y = yPosition + (1f - ap) * 5f;
        float w = width;
        float h = height;
        float r = 4f;
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
        bg = Draw.fade(bg, ap); border = Draw.fade(border, ap); txt = Draw.fade(txt, ap);

        Draw.roundRect(x, y, w, h, r, bg);
        if (((border >>> 24) & 255) > 4) Draw.roundOutline(x, y, w, h, r, 1f, border);

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

    private void drawToggle(float sx, float sy, float sw, float sh, float knob, float ap) {
        int track = on ? Theme.ACCENT : 0x30FFFFFF;
        Draw.roundRect(sx, sy, sw, sh, sh / 2f, Draw.fade(track, ap));
        float kx = sx + sh / 2f + (sw - sh) * knob;
        Draw.circle(kx, sy + sh / 2f, sh / 2f - 1.5f, Draw.fade(0xFFFFFFFF, ap));
    }
}
'''


# =====================================================================
#  2.  SIMPLER GuiModernMenu.java  (no icons)
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

        buttonList.add(new UiButton(1, pad, top,                  bw, bh, "Singleplayer").delay(40));
        buttonList.add(new UiButton(2, pad, top + 1*(bh+gap),     bw, bh, "Multiplayer").delay(70));
        buttonList.add(new UiButton(6, pad, top + 2*(bh+gap),     bw, bh, "Alt Manager").delay(100));
        buttonList.add(new UiButton(3, pad, top + 3*(bh+gap),     bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(130));
        buttonList.add(new UiButton(4, pad, top + 4*(bh+gap),     bw, bh, "Options").delay(160));
        buttonList.add(new UiButton(5, pad, top + 5*(bh+gap),     bw, bh, "Quit").style(UiButton.DANGER).delay(190));
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
#  3.  SIMPLER GuiKbOptions.java  (no icons, no glow)
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
        int bx       = cx - bw / 2;

        bHud   = new UiButton(1, bx, togglesY,                  bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(50);
        bToast = new UiButton(3, bx, togglesY + 1*(bh+gap),     bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(90);
        bLoad  = new UiButton(4, bx, togglesY + 2*(bh+gap),     bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(130);
        bDisc  = new UiButton(8, bx, togglesY + 3*(bh+gap),     bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(170);
        bFade  = new UiButton(5, bx, togglesY + 4*(bh+gap),     bw, bh, "").delay(210);

        buttonList.add(bHud);
        buttonList.add(bToast);
        buttonList.add(bLoad);
        buttonList.add(bDisc);
        buttonList.add(bFade);

        int actionY = togglesY + togglesH + actionsGap;
        int ag = 8;
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
#  4.  BETTER Hud.java  (smoother toast animation)
# =====================================================================
HUD = r'''package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBSample;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.ScaledResolution;

public final class Hud {
    private Hud() {}

    /* ------------------ toast records ------------------ */
    private static final long IN_MS   = 320L;   /* slide-in duration  */
    private static final long HOLD_MS = 2600L;  /* time before fade   */
    private static final long OUT_MS  = 700L;   /* fade-out duration  */
    private static final long LIFE_MS = IN_MS + HOLD_MS + OUT_MS;

    private static final class Toast {
        final String text;
        final int    color;
        final long   born;
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

    /* easing helpers */
    private static float easeOutCubic(float t) {
        t = Draw.clamp(t);
        float u = 1f - t;
        return 1f - u * u * u;
    }
    private static float easeInCubic(float t) {
        t = Draw.clamp(t);
        return t * t * t;
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
        boolean goal  = t.getGoal() > 0;
        int x = 6, y = 6, w = 156;
        int h = goal ? 56 : 48;

        Draw.roundRect(x, y, w, h, 6f, Draw.fade(Theme.SURFACE, a));
        Draw.roundOutline(x, y, w, h, 6f, 1f, Draw.fade(Theme.BORDER, a));
        Draw.rect(x + 1, y + 1, 3, h - 2,
                  Draw.fade(t.isRecording() ? Theme.ACCENT : Theme.MUTED, a));

        Draw.left("KB CLIENT", x + 10, y + 12, Draw.fade(Theme.TEXT, a), 0.85f, false);
        Draw.right(t.isRecording() ? "REC" : "PAUSED",
                   x + w - 10, y + 12,
                   Draw.fade(t.isRecording() ? Theme.GOOD : Theme.WARN, a), 0.8f, false);

        if (last != null) {
            Draw.left("H " + KBProfile.f(last.h, 4) + "   V " + KBProfile.f(last.vy, 4),
                      x + 10, y + 26, Draw.fade(Theme.SOFT, a), 0.9f, false);
        } else {
            Draw.left("Waiting for hits...",
                      x + 10, y + 26, Draw.fade(Theme.MUTED, a), 0.9f, false);
        }
        Draw.left(pr.used + " / " + pr.total + " samples",
                  x + 10, y + 38, Draw.fade(Theme.MUTED, a), 0.75f, false);

        if (goal) {
            Draw.bar(x + 10, y + h - 10, w - 20, 3,
                     t.getSessionHits() / (double) t.getGoal(),
                     Draw.fade(Theme.SURFACE3, a), Draw.fade(Theme.ACCENT, a));
        }

        /* ------------- toasts with improved animation ------------- */
        long now = System.currentTimeMillis();
        for (int i = toasts.size() - 1; i >= 0; i--) {
            if (now - toasts.get(i).born > LIFE_MS + 100) toasts.remove(i);
        }

        int ty = y + h + 6;
        for (int i = toasts.size() - 1; i >= 0; i--) {
            Toast to = toasts.get(i);
            long age = now - to.born;

            /* phase progress: 0..1 in, then hold, then 0..1 out */
            float inP, outP;
            if (age < IN_MS) {
                inP  = age / (float) IN_MS;
                outP = 0f;
            } else if (age < IN_MS + HOLD_MS) {
                inP  = 1f;
                outP = 0f;
            } else {
                inP  = 1f;
                outP = Math.min(1f, (age - IN_MS - HOLD_MS) / (float) OUT_MS);
            }

            float easedIn  = easeOutCubic(inP);
            float easedOut = easeInCubic(outP);

            float visibility = (1f - easedOut) * easedIn * a;
            /* slide in from left (16px) then a small overshoot-free settle */
            float slideX = -(1f - easedIn) * 18f;
            /* gentle upward drift on exit */
            float slideY = -easedOut * 6f;
            /* slight scale pop on entry */
            float sc = 0.94f + 0.06f * easedIn;

            int tw = Draw.width(to.text, 0.85f) + 16;
            int bx = x + (int) slideX;
            int by = ty + (int) slideY;
            int bw = (int) (tw * sc);
            int bh = (int) (16 * sc);

            Draw.roundRect(bx, by, bw, bh, 4f,
                           Draw.alpha(Theme.SURFACE, 0.95f * visibility));
            Draw.roundOutline(bx, by, bw, bh, 4f, 1f,
                              Draw.alpha(Theme.BORDER, visibility));

            int al = (int)(255 * visibility);
            if (al > 4) {
                Draw.left(to.text, bx + 8, by + bh / 2f,
                          (al << 24) | (to.color & 0xFFFFFF), 0.85f, false);
            }
            ty += 18;
        }
    }
}
'''


# =====================================================================
#  5.  TransparentOverlays.java  (scoreboard / tab / chat backgrounds)
# =====================================================================
TRANSPARENT_OVERLAYS = r'''package com.oryvex.kbclient;

import java.lang.reflect.Field;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiIngame;
import net.minecraft.client.gui.GuiNewChat;
import net.minecraft.client.gui.ScaledResolution;
import net.minecraft.scoreboard.Scoreboard;
import net.minecraft.scoreboard.ScoreboardObjective;
import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

/**
 * Installs a custom GuiIngame that renders the scoreboard, tab list and chat
 * WITHOUT the semi-transparent dark background panels.
 *
 * We do NOT remove the content - we only skip the background rects.
 *
 * The vanilla methods are essentially copied and re-implemented with every
 * drawRect(...) that used 0x50000000 / 0x60000000 removed.
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
                    Minecraft.class, mc, replacement, "ingameGUI", "field_71456_v");

            /* Replace the chat panel too, using reflection on the private field */
            try {
                GuiNewChat chat = new TransparentChat(mc);
                ObfuscationReflectionHelper.setPrivateValue(
                        GuiIngame.class, replacement, chat,
                        "persistantChatGUI", "field_73841_b");
            } catch (Throwable t) {
                KBClientMod.logger.warn("[KBClient] chat swap failed: " + t);
            }

            MinecraftForge.EVENT_BUS.register(new TabHider());

            KBClientMod.logger.info("[KBClient] transparent overlays installed");
        } catch (Throwable t) {
            KBClientMod.logger.error("[KBClient] TransparentOverlays failed: " + t);
        }
    }

    /* ===================== GuiIngame subclass ===================== */
    public static class TransparentGuiIngame extends GuiIngame {
        private final Minecraft mcRef;

        public TransparentGuiIngame(Minecraft mc) {
            super(mc);
            this.mcRef = mc;
        }

        /* Scoreboard sidebar: same as vanilla, no background rects. */
        @Override
        protected void renderScoreboard(ScoreboardObjective objective, ScaledResolution sr) {
            if (objective == null) return;
            Scoreboard sb = objective.getScoreboard();
            java.util.Collection<net.minecraft.scoreboard.Score> sorted =
                    sb.getSortedScores(objective);

            java.util.List<net.minecraft.scoreboard.Score> list =
                    new java.util.ArrayList<net.minecraft.scoreboard.Score>();
            for (net.minecraft.scoreboard.Score s : sorted) {
                String n = s.getPlayerName();
                if (n != null && !n.startsWith("#")) list.add(s);
            }
            if (list.size() > 15) list = list.subList(list.size() - 15, list.size());
            if (list.isEmpty()) return;

            int width = this.mc.fontRendererObj.getStringWidth(objective.getDisplayName());
            for (net.minecraft.scoreboard.Score s : list) {
                net.minecraft.scoreboard.ScoreboardTeam team =
                        sb.getPlayersTeam(s.getPlayerName());
                net.minecraft.util.IChatComponent c =
                        net.minecraft.scoreboard.ScorePlayerTeam.formatPlayerName(team, s.getPlayerName());
                width = Math.max(width, this.mc.fontRendererObj.getStringWidth(c.getFormattedText()));
            }

            int lineH  = this.mc.fontRendererObj.FONT_HEIGHT;
            int totalH = list.size() * lineH;
            int y0     = sr.getScaledHeight() / 2 + totalH / 3;
            int right  = sr.getScaledWidth() - 3;
            int left   = right - width;

            int idx = 0;
            for (net.minecraft.scoreboard.Score s : list) {
                idx++;
                net.minecraft.scoreboard.ScoreboardTeam team =
                        sb.getPlayersTeam(s.getPlayerName());
                String name = net.minecraft.scoreboard.ScorePlayerTeam
                        .formatPlayerName(team, s.getPlayerName()).getFormattedText();
                String pts  = "\u00a7c" + s.getScorePoints();
                int y = y0 - idx * lineH;

                /* NOTE: no drawRect background here on purpose */
                this.mc.fontRendererObj.drawString(name, left, y, 0x20FFFFFF);
                this.mc.fontRendererObj.drawString(
                        pts,
                        right + 2 - this.mc.fontRendererObj.getStringWidth(pts),
                        y, 0x20FFFFFF);

                if (idx == list.size()) {
                    String title = objective.getDisplayName().getFormattedText();
                    this.mc.fontRendererObj.drawString(
                            title,
                            left + width / 2 - this.mc.fontRendererObj.getStringWidth(title) / 2,
                            y - lineH, 0x20FFFFFF);
                }
            }
        }

        /* The tab list is fully cancelled by TabHider below. */
        @Override
        protected void renderPlayerList(ScaledResolution sr, Scoreboard sb) {
            /* no-op: TabHider cancels the event so this method never draws a bg */
        }
    }

    /* ===================== Chat subclass ===================== */
    public static class TransparentChat extends GuiNewChat {
        private final Minecraft mcRef;

        private static Field F_LINES;
        private static Field F_SCROLL;

        static {
            try {
                F_LINES  = ObfuscationReflectionHelper.findField(
                        GuiNewChat.class, "drawnChatLines", "field_146253_i");
                F_SCROLL = ObfuscationReflectionHelper.findField(
                        GuiNewChat.class, "scrollPos", "field_146250_j");
                F_LINES.setAccessible(true);
                F_SCROLL.setAccessible(true);
            } catch (Throwable ignored) { }
        }

        public TransparentChat(Minecraft mc) {
            super(mc);
            this.mcRef = mc;
        }

        @Override
        public void drawChat(int updateCounter) {
            if (this.mcRef.gameSettings.chatVisibility ==
                    net.minecraft.entity.player.EntityPlayer.EnumChatVisibility.HIDDEN) return;

            if (F_LINES == null) {
                /* fallback: vanilla behaviour if reflection failed */
                super.drawChat(updateCounter);
                return;
            }

            try {
                @SuppressWarnings("unchecked")
                java.util.List<net.minecraft.client.gui.ChatLine> lines =
                        (java.util.List<net.minecraft.client.gui.ChatLine>) F_LINES.get(this);
                int scrollPos = F_SCROLL.getInt(this);

                int lineCount = this.getLineCount();
                boolean chatOpen = this.getChatOpen();
                int total = lines.size();
                float chatOpacity = this.mcRef.gameSettings.chatOpacity * 0.9F + 0.1F;

                if (total <= 0) return;

                float scale = this.getChatScale();
                int boxWidth = net.minecraft.util.MathHelper.ceiling_float_int(
                        (float) this.getChatWidth() / scale);

                net.minecraft.client.renderer.GlStateManager.pushMatrix();
                net.minecraft.client.renderer.GlStateManager.translate(2.0F, 20.0F, 0.0F);
                net.minecraft.client.renderer.GlStateManager.scale(scale, scale, 1.0F);

                int drawn = 0;
                for (int i = 0; i + scrollPos < total && i < lineCount; i++) {
                    net.minecraft.client.gui.ChatLine cl = lines.get(i + scrollPos);
                    if (cl == null) continue;

                    int age = updateCounter - cl.getUpdatedCounter();
                    if (age >= 200 && !chatOpen) continue;

                    double d = (double) age / 200.0D;
                    d = 1.0D - d;
                    d = d * 10.0D;
                    d = net.minecraft.util.MathHelper.clamp_double(d, 0.0D, 1.0D);
                    d = d * d;
                    int alphaByte = (int)(255.0D * d);
                    if (chatOpen) alphaByte = 255;
                    alphaByte = (int)((float) alphaByte * chatOpacity);
                    drawn++;

                    if (alphaByte > 3) {
                        int x = 0;
                        int y = -i * 9;

                        /* >>> background rect REMOVED on purpose <<< */

                        String s = cl.getChatComponent().getFormattedText();
                        net.minecraft.client.renderer.GlStateManager.enableBlend();
                        this.mcRef.fontRendererObj.drawStringWithShadow(
                                s, (float) x, (float) (y - 8),
                                16777215 + (alphaByte << 24));
                        net.minecraft.client.renderer.GlStateManager.disableAlpha();
                        net.minecraft.client.renderer.GlStateManager.disableBlend();
                    }
                }

                /* scrolling box background also skipped */
                net.minecraft.client.renderer.GlStateManager.popMatrix();
            } catch (Throwable t) {
                /* on any error just fall back to vanilla */
                try { super.drawChat(updateCounter); } catch (Throwable ignored) { }
            }
        }
    }

    /* ===================== Tab list hider ===================== */
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
#  6.  Apply
# =====================================================================
def main():
    print("== KB Client - adder.py ==")
    print("root:", ROOT)

    if not os.path.isdir(SRC):
        print("!! Could not find", SRC)
        print("   Run this script from the project root (where build.gradle is).")
        sys.exit(1)

    print("\n[1/6] simpler UiButton")
    write(os.path.join(UI, "UiButton.java"), UIBUTTON)

    print("\n[2/6] simpler GuiModernMenu")
    write(os.path.join(UI, "GuiModernMenu.java"), GUI_MODERN_MENU)

    print("\n[3/6] simpler GuiKbOptions")
    write(os.path.join(UI, "GuiKbOptions.java"), GUI_KB_OPTIONS)

    print("\n[4/6] better Hud toasts")
    write(os.path.join(UI, "Hud.java"), HUD)

    print("\n[5/6] TransparentOverlays")
    write(os.path.join(SRC, "TransparentOverlays.java"), TRANSPARENT_OVERLAYS)

    print("\n[6/6] patch KBClientMod to install overlays")
    kbmod = os.path.join(SRC, "KBClientMod.java")
    patch(kbmod, [
        (
            "installLoading();\n            if (Settings.discordRpc) DiscordRPC.start();",
            "installLoading();\n            com.oryvex.kbclient.TransparentOverlays.install();\n            if (Settings.discordRpc) DiscordRPC.start();"
        ),
        (
            "installLoading();\n            DiscordRPC.start();",
            "installLoading();\n            com.oryvex.kbclient.TransparentOverlays.install();\n            DiscordRPC.start();"
        ),
        (
            "installLoading();\n            try {\n                Minecraft mcF = Minecraft.getMinecraft();",
            "installLoading();\n            com.oryvex.kbclient.TransparentOverlays.install();\n            try {\n                Minecraft mcF = Minecraft.getMinecraft();"
        ),
    ])

    print("\n== done ==")
    print("Files modified get a  <name>.bak_<timestamp>  backup next to them.")
    print("Build with:  ./gradlew build")


if __name__ == "__main__":
    main()