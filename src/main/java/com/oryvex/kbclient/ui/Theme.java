
package com.oryvex.kbclient.ui;

/** Colour palette + selectable accent themes (Settings.theme). */
public final class Theme {
    private Theme() {}

    // ---- surfaces ---------------------------------------------------------
    public static final int BG0 = 0xFF05060B;
    public static final int BG1 = 0xFF0B0D16;
    public static final int SURFACE = 0xEB0D0F17;   // window / big card
    public static final int SURFACE2 = 0xFF141722;  // raised card
    public static final int SURFACE3 = 0xFF1C2030;  // hover / pressed
    public static final int GLASS = 0xA6090B12;     // translucent panel
    public static final int FILL = 0x16FFFFFF;      // subtle light fill (buttons)
    public static final int FILL_HI = 0x2AFFFFFF;   // hovered light fill
    public static final int STROKE = 0x1FFFFFFF;
    public static final int STROKE_HI = 0x47FFFFFF;

    // ---- status ------------------------------------------------------------
    public static final int GOOD = 0xFF34D399;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD = 0xFFFB7185;

    // ---- text ----------------------------------------------------------------
    public static final int TEXT = 0xFFF4F6FB;
    public static final int SOFT = 0xFFB4BCCF;
    public static final int MUTED = 0xFF7C86A2;
    public static final int DIM = 0xFF4A5169;

    // ---- type scale (GUI pixels) --------------------------------------------
    public static final float T_XS = 7f;
    public static final float T_SM = 8f;
    public static final float T_MD = 9f;
    public static final float T_LG = 11f;
    public static final float T_XL = 14f;

    /** Minecraft colour-code prefix (chat only). */
    public static final String S = "\u00a7";

    // ---- accent themes ------------------------------------------------------
    public static final String[] THEME_NAMES = { "Ocean", "Violet", "Sunset", "Mint", "Rose", "Mono" };
    private static final int[][] PAL = {
        { 0xFF38BDF8, 0xFF6366F1 },
        { 0xFFA78BFA, 0xFFEC4899 },
        { 0xFFFB923C, 0xFFF43F5E },
        { 0xFF34D399, 0xFF22D3EE },
        { 0xFFF472B6, 0xFFFB7185 },
        { 0xFFE5E7EB, 0xFF94A3B8 }
    };

    private static int idx() {
        int t = Settings.theme;
        return t < 0 ? 0 : (t >= PAL.length ? PAL.length - 1 : t);
    }

    public static int accent() { return PAL[idx()][0]; }
    public static int accent2() { return PAL[idx()][1]; }
    public static int accentMid() { return Draw.lerp(accent(), accent2(), 0.5f); }

    /** accent -> accent2 -> accent ping-pong that slowly flows over time; offset 0..1 shifts the phase. */
    public static int flow(float offset) {
        float p = ((System.currentTimeMillis() % 7000L) / 7000f + offset) % 1f;
        if (p < 0f) p += 1f;
        float tri = p < 0.5f ? p * 2f : (1f - p) * 2f;
        return Draw.lerp(accent(), accent2(), tri);
    }

    public static float phase() { return (System.currentTimeMillis() % 7000L) / 7000f; }
    public static final int PANEL = 0xFF121A29;
    public static final int PANEL2 = 0xFF182235;
    public static final int PANEL3 = 0xFF22304A;
    public static final int BORDER = 0xFF25324B;
    public static final int BORDER_HI = 0xFF3B5078;
    public static final int ACCENT = 0xFF22D3EE;
    public static final int ACCENT_DK = 0xFF0E7490;
    public static final int ACCENT2 = 0xFFA78BFA;
}
