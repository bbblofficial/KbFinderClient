package com.oryvex.kbclient.ui;

/** Flat colour palette. No gradients, no glows. */
public final class Theme {
    private Theme() {}

    // ---- backgrounds ----
    public static final int BG0   = 0xFF0A0E14;
    public static final int BG1   = 0xFF11161F;

    // ---- surfaces ----
    public static final int SURFACE   = 0xFF161B24;   // main panels
    public static final int SURFACE2  = 0xFF1D232E;   // raised cards
    public static final int SURFACE3  = 0xFF252C38;   // hovered
    public static final int BORDER    = 0xFF2A323E;   // 1px outline
    public static final int BORDER_HI = 0xFF3A4453;   // hovered outline

    // ---- legacy aliases ----
    public static final int PANEL   = 0xFF161B24;
    public static final int PANEL2  = 0xFF1D232E;
    public static final int PANEL3  = 0xFF252C38;
    public static final int GLASS   = 0xFF161B24;
    public static final int FILL    = 0x14FFFFFF;
    public static final int FILL_HI = 0x22FFFFFF;
    public static final int STROKE  = 0x1FFFFFFF;
    public static final int STROKE_HI = 0x33FFFFFF;

    // ---- status ----
    public static final int GOOD = 0xFF4ADE80;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD  = 0xFFF87171;

    // ---- text ----
    public static final int TEXT  = 0xFFF1F5F9;
    public static final int SOFT  = 0xFFCBD5E1;
    public static final int MUTED = 0xFF94A3B8;
    public static final int DIM   = 0xFF64748B;

    // ---- type scale ----
    public static final float T_XS = 0.75f;
    public static final float T_SM = 0.85f;
    public static final float T_MD = 1.00f;
    public static final float T_LG = 1.25f;
    public static final float T_XL = 1.60f;

    public static final String S = "\u00a7";

    // ---- single accent (flat) ----
    public static final int ACCENT    = 0xFF3B82F6;   // blue
    public static final int ACCENT_HI = 0xFF60A5FA;
    public static final int ACCENT_DK = 0xFF1E40AF;
    public static final int ACCENT2   = 0xFF3B82F6;

    public static String[] THEME_NAMES = { "Blue" };

    public static int accent()  { return ACCENT; }
    public static int accent2() { return ACCENT; }
    public static int accentMid() { return ACCENT; }
    public static int flow(float offset) { return ACCENT; }
    public static float phase() { return 0f; }
}
