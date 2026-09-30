package com.oryvex.kbclient.ui;

import java.awt.Color;

/** The custom loading screen artwork (used by the loading renderer and the terrain overlay). */
public final class LoadingArt {
    private LoadingArt() {}

    private static final String[] TIPS = {
        "Press Right Shift in-game to open the Knockback Analyzer.",
        "Get hit by a walking AND a sprinting player to separate HORIZONTAL from EXTRA-HORIZONTAL.",
        "Get hit while falling to measure VERTICAL when Y-LIMIT clamps it.",
        "Use /kb import to compare a Carbon YAML against your detected profile.",
        "Every value in the analyzer carries a source tag: MEAS, EST, DEF or FILE."
    };

    /** pct < 0 = indeterminate */
    public static void draw(int w, int h, String title, String sub, int pct) {
        
        Draw.blend();
        Draw.vgradient(w, h, Theme.BG0, Theme.BG1);
        if (Settings.particles) {
            Draw.particles(w, h, 60, 0x22D3EE, 0.35f);
            Draw.particles(w, h, 20, 0xA78BFA, 0.30f);
        }
        float t = (System.currentTimeMillis() % 100000L) / 1000f;
        int cx = w / 2, cy = h / 2;

        // logo
        String logo = "ORYVEX";
        float sc = 3f;
        float tx = cx - Draw.font().getStringWidth(logo) * sc / 2f;
        int ly = cy - 70;
        for (int i = 0; i < logo.length(); i++) {
            String ch = logo.substring(i, i + 1);
            float hue = 0.50f + 0.17f * (0.5f + 0.5f * (float) Math.sin(t * 0.9f + i * 0.6f));
            Draw.text(ch, tx, ly, Color.HSBtoRGB(hue, 0.55f, 1f) | 0xFF000000, sc, true);
            tx += Draw.font().getStringWidth(ch) * sc;
        }
        Draw.centered("K N O C K B A C K   C L I E N T", cx, ly + 28, Theme.MUTED, 0.8f, false);

        // orbiting comet spinner
        int sy = cy + 2;
        Draw.roundRect(cx - 16, sy - 16, 32, 32, 16, Draw.alpha(0x22D3EE, 0.06f));
        for (int i = 0; i < 12; i++) {
            double ang = t * 3.4 - i * 0.5;
            int dx = (int) Math.round(Math.cos(ang) * 13);
            int dy = (int) Math.round(Math.sin(ang) * 13);
            float a = 1f - i / 12f;
            int sz = i < 3 ? 3 : 2;
            Draw.rect(cx + dx - sz / 2, sy + dy - sz / 2, sz, sz, Draw.alpha(i % 2 == 0 ? 0x22D3EE : 0xA78BFA, a));
        }

        // text + bar
        String ttl = (title == null || title.isEmpty()) ? "Loading" : title;
        Draw.centered(ttl, cx, cy + 26, Theme.TEXT, 1f, true);
        if (sub != null && !sub.isEmpty()) Draw.centered(sub, cx, cy + 38, Theme.MUTED, 0.85f, false);

        int bw = 180, bx = cx - bw / 2, by = cy + 54;
        Draw.roundRect(bx, by, bw, 4, 2, Theme.PANEL3);
        if (pct >= 0) {
            Draw.roundRect(bx, by, Math.max(2, bw * Math.min(100, pct) / 100), 4, 2, Theme.ACCENT);
            Draw.centered(pct + "%", cx, by + 8, Theme.SOFT, 0.8f, false);
        } else {
            float p = (t * 0.9f) % 1f;
            int seg = 56;
            int sx = bx + (int) ((bw + seg) * p) - seg;
            int x0 = Math.max(bx, sx), x1 = Math.min(bx + bw, sx + seg);
            if (x1 > x0) Draw.roundRect(x0, by, x1 - x0, 4, 2, Theme.ACCENT);
        }

        // tip
        String tip = "TIP  " + TIPS[(int) ((System.currentTimeMillis() / 4500L) % TIPS.length)];
        Draw.centered(tip, cx, h - 22, Theme.DIM, 0.8f, false);
        Draw.text("KB Client 3.0", 6, h - 12, Theme.DIM, 0.75f, false);
    
    }
}
