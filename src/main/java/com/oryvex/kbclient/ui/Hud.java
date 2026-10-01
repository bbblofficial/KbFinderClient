package com.oryvex.kbclient.ui;

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
