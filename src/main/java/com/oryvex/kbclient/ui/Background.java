
package com.oryvex.kbclient.ui;

import java.util.Random;

/** Animated backdrop: gradient base + drifting aurora glows + cursor-aware plexus particles + vignette. */
public final class Background {
    private Background() {}

    private static final int MAXP = 120;
    private static final float[] px = new float[MAXP], py = new float[MAXP], vx = new float[MAXP], vy = new float[MAXP];
    private static int count, lastW = -1, lastH = -1;
    private static long lastNs = System.nanoTime();
    private static final Random R = new Random(7L);

    private static void blob(int w, int h, float t, float sp, float ph, float sp2, float ph2, float rf, int color, float am) {
        float cx = w * (0.5f + 0.40f * (float) Math.sin(t * sp + ph));
        float cy = h * (0.5f + 0.36f * (float) Math.cos(t * sp2 + ph2));
        Draw.radial(cx, cy, Math.max(w, h) * rf, Draw.fade(color, am), true);
    }

    private static void seed(int w, int h, int target) {
        count = target;
        for (int i = 0; i < count; i++) {
            px[i] = R.nextFloat() * w;
            py[i] = R.nextFloat() * h;
            float sp = 6f + R.nextFloat() * 14f;
            double a = R.nextDouble() * Math.PI * 2.0;
            vx[i] = (float) Math.cos(a) * sp;
            vy[i] = (float) Math.sin(a) * sp;
        }
        lastW = w;
        lastH = h;
    }

    public static void draw(int w, int h, int mx, int my, boolean inWorld, float intensity) {
        float t = (System.currentTimeMillis() % 1000000L) / 1000f;
        if (inWorld) Draw.vgrad(0, 0, w, h, 0xD6070A12, 0xEA0E1424);
        else Draw.vgrad(0, 0, w, h, Theme.BG0, Theme.BG1);

        if (Settings.aurora) {
            float k = (inWorld ? 0.55f : 1f) * intensity;
            int a1 = Theme.accent(), a2 = Theme.accent2(), am = Theme.accentMid();
            blob(w, h, t, 0.11f, 0.0f, 0.09f, 1.3f, 0.62f, a1, 0.20f * k);
            blob(w, h, t, 0.08f, 2.1f, 0.12f, 0.4f, 0.58f, a2, 0.18f * k);
            blob(w, h, t, 0.13f, 4.0f, 0.07f, 2.7f, 0.50f, am, 0.13f * k);
            blob(w, h, t, 0.06f, 5.2f, 0.10f, 3.9f, 0.72f, a2, 0.10f * k);
        }

        // vignette
        float vh = Math.min(w, h) * 0.30f;
        Draw.vgrad(0, 0, w, vh, 0x66000000, 0x00000000);
        Draw.vgrad(0, h - vh, w, vh, 0x00000000, 0x77000000);
        Draw.hgrad(0, 0, vh, h, 0x55000000, 0x00000000);
        Draw.hgrad(w - vh, 0, vh, h, 0x00000000, 0x55000000);

        if (Settings.particles && Settings.density > 0) particles(w, h, mx, my, intensity);
    }

    private static void particles(int w, int h, int mx, int my, float intensity) {
        int target = (int) (Math.max(18, Math.min(90, (w * h) / 6000)) * (Settings.density / 100f));
        target = Math.max(0, Math.min(MAXP, target));
        if (w != lastW || h != lastH || target != count) seed(w, h, target);

        long now = System.nanoTime();
        float dt = Math.min(0.05f, (now - lastNs) / 1.0e9f);
        lastNs = now;

        for (int i = 0; i < count; i++) {
            px[i] += vx[i] * dt;
            py[i] += vy[i] * dt;
            if (px[i] < -12) px[i] = w + 12; else if (px[i] > w + 12) px[i] = -12;
            if (py[i] < -12) py[i] = h + 12; else if (py[i] > h + 12) py[i] = -12;
        }

        float link = Math.max(55f, Math.min(115f, Math.min(w, h) * 0.24f));
        int c = Theme.accent();
        for (int i = 0; i < count; i++) {
            for (int j = i + 1; j < count; j++) {
                float dx = px[i] - px[j], dy = py[i] - py[j];
                float d2 = dx * dx + dy * dy;
                if (d2 < link * link) {
                    float a = (1f - (float) Math.sqrt(d2) / link) * 0.32f * intensity;
                    Draw.line(px[i], py[i], px[j], py[j], 0.7f, Draw.alpha(c, a));
                }
            }
            float mdx = px[i] - mx, mdy = py[i] - my;
            float md = mdx * mdx + mdy * mdy;
            float ml = link * 1.25f;
            if (md < ml * ml) {
                float a = (1f - (float) Math.sqrt(md) / ml) * 0.5f * intensity;
                Draw.line(px[i], py[i], mx, my, 0.8f, Draw.alpha(Theme.accent2(), a));
            }
        }

        for (int i = 0; i < count; i++) {
            float tw = 0.55f + 0.45f * (float) Math.sin(System.currentTimeMillis() / 700.0 + i * 1.7);
            Draw.circle(px[i], py[i], 1.25f, Draw.alpha(0xFFFFFFFF, 0.55f * tw * intensity));
        }
    }
}
