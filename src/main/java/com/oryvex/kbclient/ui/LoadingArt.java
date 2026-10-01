package com.oryvex.kbclient.ui;

public final class LoadingArt {
    private LoadingArt() {}

    private static final String[] TIPS = {
        "Press Right Shift in-game to open the Knockback Analyzer.",
        "Get hit by a walking AND a sprinting player to separate HORIZONTAL from EXTRA-HORIZONTAL.",
        "Get hit while falling to measure VERTICAL when Y-LIMIT clamps it.",
        "Use /kb import to compare a Carbon YAML against your detected profile."
    };

    public static void draw(int w, int h, String title, String sub, int pct) {
        Draw.rect(0, 0, w, h, Theme.BG0);

        int cx = w / 2;
        int cy = h / 2;

        // logo
        float scale = 3f;
        Draw.centered("ORYVEX", cx, cy - 70, Theme.TEXT, scale, false);
        Draw.centered("K N O C K B A C K   C L I E N T", cx,
                cy - 70 + Draw.lineH(scale) + 10, Theme.MUTED, 0.85f, false);

        // spinner (simple rotating dots)
        long t = System.currentTimeMillis();
        int sy = cy + 10;
        int dots = 8;
        for (int i = 0; i < dots; i++) {
            double ang = (t / 300.0) + (Math.PI * 2 * i) / dots;
            int dx = (int)Math.round(Math.cos(ang) * 14);
            int dy = (int)Math.round(Math.sin(ang) * 14);
            float fa = 0.25f + 0.75f * (i / (float)dots);
            Draw.circle(cx + dx, sy + dy, 2f, Draw.alpha(Theme.ACCENT, fa));
        }

        // text
        String ttl = (title == null || title.isEmpty()) ? "Loading" : title;
        Draw.centered(ttl, cx, cy + 44, Theme.TEXT, 1.0f, false);
        if (sub != null && !sub.isEmpty()) {
            Draw.centered(sub, cx, cy + 44 + Draw.lineH(1.0f) + 6, Theme.MUTED, 0.85f, false);
        }

        // progress bar
        int bw = 200, bx = cx - bw / 2, by = cy + 78;
        Draw.roundRect(bx, by, bw, 4, 2, Theme.SURFACE3);
        if (pct >= 0) {
            int fw = Math.max(2, bw * Math.min(100, pct) / 100);
            Draw.roundRect(bx, by, fw, 4, 2, Theme.ACCENT);
            Draw.centered(pct + "%", cx, by + 14, Theme.MUTED, 0.8f, false);
        } else {
            // indeterminate
            double p = (t % 1600L) / 1600.0;
            int seg = 60;
            int sx = bx + (int)((bw + seg) * p) - seg;
            int x0 = Math.max(bx, sx);
            int x1 = Math.min(bx + bw, sx + seg);
            if (x1 > x0) Draw.roundRect(x0, by, x1 - x0, 4, 2, Theme.ACCENT);
        }

        // tip
        String tip = "TIP  " + TIPS[(int)((System.currentTimeMillis() / 4500L) % TIPS.length)];
        Draw.centered(tip, cx, h - 24, Theme.DIM, 0.85f, false);
        Draw.left("KB Client 3.0", 8, h - 10, Theme.DIM, 0.75f, false);
    }
}
