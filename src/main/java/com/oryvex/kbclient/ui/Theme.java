package com.oryvex.kbclient.ui;

/** Strict Black & White (Monochrome) colour palette. */
public final class Theme {
    private Theme() {}
    
    // ---- backgrounds (Pure Black to Dark Gray) ----
    public static final int BG0   = 0xFF000000; // Pure Black
    public static final int BG1   = 0xFF080808; // Almost Black
    
    // ---- surfaces (Dark Grays) ----
    public static final int SURFACE   = 0xFF121212;
    public static final int SURFACE2  = 0xFF1A1A1A;
    public static final int SURFACE3  = 0xFF242424;
    
    // Legacy aliases
    public static final int PANEL   = SURFACE;
    public static final int PANEL2  = SURFACE2;
    public static final int PANEL3  = SURFACE3;
    public static final int GLASS   = 0xE6000000; // Semi-transparent black
    
    // ---- borders (Grays) ----
    public static final int BORDER    = 0xFF2A2A2A;
    public static final int BORDER_HI = 0xFF444444;
    
    // ---- status (Using brightness for contrast) ----
    public static final int GOOD = 0xFFFFFFFF; // Pure White
    public static final int WARN = 0xFFAAAAAA; // Light Gray
    public static final int BAD  = 0xFF555555; // Mid Gray
    
    // ---- text ----
    public static final int TEXT  = 0xFFFFFFFF; // Pure White
    public static final int SOFT  = 0xFFDDDDDD; // Off-white
    public static final int MUTED = 0xFF777777; // Mid Gray
    public static final int DIM   = 0xFF444444; // Dark Gray
    
    // ---- accent (Monochrome accents) ----
    public static final int ACCENT    = 0xFFFFFFFF; // Pure White
    public static final int ACCENT_DK = 0xFF888888; // Mid-Light Gray
    public static final int ACCENT2   = 0xFFBBBBBB; // Light Gray
    
    // ---- Typography Scale ----
    public static final float T_XS = 0.75f;
    public static final float T_SM = 0.85f;
    public static final float T_MD = 1.00f;
    public static final float T_LG = 1.25f;
    public static final float T_XL = 1.60f;
    
    public static final String S = "\u00a7";
}
