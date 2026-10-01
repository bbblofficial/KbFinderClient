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
    private static final class Toast { final String text; final int color; final long born; Toast(String t, int c) { text = t; color = c; born = System.currentTimeMillis(); } }
    private static final List<Toast> toasts = new ArrayList<Toast>();
    private static float alpha = 0f;
    private static long lastNs = System.nanoTime();
    public static void push(String text, int color) { if (!Settings.toasts) return; toasts.add(new Toast(text, color)); while (toasts.size() > 4) toasts.remove(0); }
    public static void render(Minecraft mc, KBTracker t) {
        ScaledResolution res = new ScaledResolution(mc);
        if (Settings.watermark) Draw.right("Created by muvixo", res.getScaledWidth() - 6, res.getScaledHeight() - 10, Theme.DIM, 0.7f, false);
        long ns = System.nanoTime();
        float dt = Math.min(0.1f, (ns - lastNs) / 1.0e9f);
        lastNs = ns;
        alpha += ((Settings.hud ? 1f : 0f) - alpha) * Math.min(1f, dt * 8f);
        if (alpha < 0.03f) return;
        float a = alpha;
        KBProfile pr = t.getProfile();
        KBSample last = t.getLast();
        boolean goal = t.getGoal() > 0;
        int x = 6, y = 6, w = 140;
        int h = goal ? 50 : 42;
        Draw.panel(x, y, w, h, 4, Draw.fade(Theme.SURFACE, a), Draw.fade(Theme.BORDER, a));
        Draw.left("KB CLIENT", x + 8, y + 10, Draw.fade(Theme.TEXT, a), 0.85f, false);
        Draw.right(t.isRecording() ? "REC" : "PAUSED", x + w - 8, y + 10, Draw.fade(t.isRecording() ? Theme.GOOD : Theme.WARN, a), 0.8f, false);
        if (last != null) Draw.left("H " + KBProfile.f(last.h, 4) + " V " + KBProfile.f(last.vy, 4), x + 8, y + 22, Draw.fade(Theme.SOFT, a), 0.85f, false);
        else Draw.left("Waiting...", x + 8, y + 22, Draw.fade(Theme.MUTED, a), 0.85f, false);
        Draw.left(pr.used + " / " + pr.total, x + 8, y + 32, Draw.fade(Theme.MUTED, a), 0.75f, false);
        if (goal) Draw.bar(x + 8, y + h - 8, w - 16, 2, t.getSessionHits() / (double) t.getGoal(), Draw.fade(Theme.SURFACE3, a), Draw.fade(Theme.ACCENT, a));
        long now = System.currentTimeMillis();
        for (int i = toasts.size() - 1; i >= 0; i--) if (now - toasts.get(i).born > 3600) toasts.remove(i);
        int ty = y + h + 4;
        for (int i = toasts.size() - 1; i >= 0; i--) {
            Toast to = toasts.get(i);
            long age = now - to.born;
            float in = age < 160 ? age / 160f : 1f;
            float fade = (age > 2800 ? 1f - (age - 2800) / 800f : 1f) * in * a;
            int tw = Draw.width(to.text, 0.85f) + 12;
            Draw.panel(x, ty, tw, 14, 3, Draw.alpha(Theme.SURFACE, 0.95f * fade), Draw.alpha(Theme.BORDER, fade));
            int al = (int)(255 * fade);
            if (al > 4) Draw.left(to.text, x + 6, ty + 7, (al << 24) | (to.color & 0xFFFFFF), 0.85f, false);
            ty += 16;
        }
    }
}