package com.oryvex.kbclient.ui;

/** Flat colour palette. Simplified for clarity. */
public final class Theme {
    private Theme() {}

    // ---- backgrounds ----
    public static final int BG0   = 0xFF0A0E14;
    public static final int BG1   = 0xFF11161F;

    // ---- surfaces ----
    public static final int SURFACE   = 0xFF161B24;
    public static final int SURFACE2  = 0xFF1D232E;
    public static final int SURFACE3  = 0xFF252C38;
    
    // Legacy aliases for compatibility
    public static final int PANEL   = SURFACE;
    public static final int PANEL2  = SURFACE2;
    public static final int PANEL3  = SURFACE3;
    public static final int GLASS   = SURFACE;

    public static final int BORDER    = 0xFF2A323E;
    public static final int BORDER_HI = 0xFF3A4453;

    // ---- status ----
    public static final int GOOD = 0xFF4ADE80;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD  = 0xFFF87171;

    // ---- text ----
    public static final int TEXT  = 0xFFF1F5F9;
    public static final int SOFT  = 0xFFCBD5E1;
    public static final int MUTED = 0xFF94A3B8;
    public static final int DIM   = 0xFF64748B;

    // ---- accent ----
    public static final int ACCENT    = 0xFF3B82F6;
    public static final int ACCENT_DK = 0xFF1E40AF;
    public static final int ACCENT2   = 0xFFA78BFA; // Secondary accent (Purple)

    public static final String S = "\u00a7";
}