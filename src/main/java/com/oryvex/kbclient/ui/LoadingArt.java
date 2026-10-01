package com.oryvex.kbclient.ui;

public final class LoadingArt {
    private LoadingArt() {}

    private static final String[] TIPS = {
        "Press Right Shift in-game to open the Knockback Analyzer.",
        "Get hit by a walking AND a sprinting player to separate HORIZONTAL from EXTRA-HORIZONTAL.",
        "Get hit while falling to measure VERTICAL when Y-LIMIT clamps it.",
        "Use /kb import to compare a Carbon YAML against your detected profile.",
        "Every value in the analyzer carries a source tag: MEAS, EST, DEF or FILE."
    };

    public static void draw(int w, int h, String title, String sub, int pct) {
        Draw.blend();
        Draw.vgradient(w, h, Theme.BG0, Theme.BG1);

        int cx = w / 2;
        int cy = h / 2;
        float t = (System.currentTimeMillis() % 100000L) / 1000f;

        // ---------- Logo ----------
        String logo = "ORYVEX";
        float scale = 3f;
        float tw = Draw.font().getStringWidth(logo) * scale;
        Draw.text(logo, cx - tw / 2f, cy - 90, Theme.TEXT, scale, true);

        Draw.centered("K N O C K B A C K   C L I E N T", cx, cy - 90 + Draw.lineH(scale) + 6,
                Theme.MUTED, 0.85f, false);

        // ---------- Spinner ----------
        int sy = cy + 4;
        Draw.roundRect(cx - 16, sy - 16, 32, 32, 16, Draw.alpha(Theme.accent(), 0.08f));
        for (int i = 0; i < 12; i++) {
            double ang = t * 3.4 - i * 0.5;
            int dx = (int) Math.round(Math.cos(ang) * 13);
            int dy = (int) Math.round(Math.sin(ang) * 13);
            float fa = 1f - i / 12f;
            int sz = i < 3 ? 3 : 2;
            Draw.rect(cx + dx - sz / 2f, sy + dy - sz / 2f, sz, sz,
                    Draw.alpha(i % 2 == 0 ? Theme.accent() : Theme.accent2(), fa));
        }

        // ---------- Status text ----------
        String ttl = (title == null || title.isEmpty()) ? "Loading" : title;
        Draw.centered(ttl, cx, cy + 40, Theme.TEXT, 1.0f, true);
        if (sub != null && !sub.isEmpty()) {
            Draw.centered(sub, cx, cy + 40 + Draw.lineH(1.0f) + 4, Theme.MUTED, 0.85f, false);
        }

        // ---------- Bar ----------
        int bw = 180, bx = cx - bw / 2, by = cy + 76;
        Draw.roundRect(bx, by, bw, 4, 2, Theme.PANEL3);
        if (pct >= 0) {
            Draw.roundRect(bx, by, Math.max(2, bw * Math.min(100, pct) / 100), 4, 2, Theme.accent());
            Draw.centered(pct + "%", cx, by + 12, Theme.SOFT, 0.8f, false);
        } else {
            float p = (t * 0.9f) % 1f;
            int seg = 56;
            int sx = bx + (int)((bw + seg) * p) - seg;
            int x0 = Math.max(bx, sx);
            int x1 = Math.min(bx + bw, sx + seg);
            if (x1 > x0) Draw.roundRect(x0, by, x1 - x0, 4, 2, Theme.accent());
        }

        // ---------- Tip ----------
        String tip = "TIP  " + TIPS[(int)((System.currentTimeMillis() / 4500L) % TIPS.length)];
        Draw.centered(tip, cx, h - 22, Theme.DIM, 0.85f, false);
        Draw.left("KB Client 3.0", 6, h - 10, Theme.DIM, 0.75f, false);
        Draw.right("Created by muvixo", w - 6, h - 10, Theme.DIM, 0.75f, false);
    }
}
