package com.oryvex.kbclient.ui;

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
