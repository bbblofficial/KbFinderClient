package com.oryvex.kbclient.ui;

/** Simple flat background — solid colour only. */
public final class Background {
    private Background() {}
    public static void draw(int w, int h, int mx, int my, boolean inWorld, float intensity) {
        Draw.rect(0, 0, w, h, Theme.BG0);
    }
}
