package com.oryvex.kbclient.ui;

import java.util.List;

public final class Ui {
    private Ui() {}

    public static int onAccent() {
        int c = Theme.accentMid();
        float lum = (0.299f * ((c >> 16) & 255) + 0.587f * ((c >> 8) & 255) + 0.114f * (c & 255)) / 255f;
        return lum > 0.66f ? 0xFF0A0C14 : 0xFFFFFFFF;
    }

    public static void toggle(float x, float cy, float knob, float alpha) {
        float w = 24f, h = 12f, y = cy - h / 2f;
        int off = Draw.fade(0x38FFFFFF, alpha);
        int c1 = Draw.lerp(off, Draw.fade(Theme.accent(), alpha), knob);
        int c2 = Draw.lerp(off, Draw.fade(Theme.accent2(), alpha), knob);
        Draw.roundRect(x, y, w, h, h / 2f, c1);
        Draw.circle(x + 6f + (w - 12f) * knob, cy, 4.2f, Draw.fade(0xFFFFFFFF, alpha));
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
