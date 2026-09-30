package com.oryvex.kbclient.ui;

import net.minecraft.client.gui.Gui;

/** Shared fade timing + full-screen fade overlays. */
public final class Fade {
    private Fade() {}

    /** overlay for vanilla screens (fade-in when a screen opens) */
    public static final Fader screen = new Fader();
    /** overlay over the game world (join world, closing a screen) */
    public static final Fader world = new Fader();

    public static long ms() {
        switch (Settings.fade) {
            case 0: return 0L;
            case 1: return 140L;
            case 2: return 260L;
            default: return 420L;
        }
    }

    public static float ease(float t) {
        t = Draw.clamp(t);
        return t * t * (3f - 2f * t);
    }

    public static final class Fader {
        private long start;
        private long dur;
        private float from;

        public void trigger(float from) { trigger(from, ms()); }

        public void trigger(float from, long ms) {
            this.from = from;
            this.dur = ms;
            this.start = System.currentTimeMillis();
        }

        public float alpha() {
            if (dur <= 0) return 0f;
            float t = (System.currentTimeMillis() - start) / (float) dur;
            if (t >= 1f || t < 0f) return 0f;
            return from * (1f - ease(t));
        }

        public void draw(int w, int h) {
            float a = alpha();
            if (a > 0.004f) Gui.drawRect(0, 0, w, h, ((int) (a * 255f)) << 24);
        }
    }
}
