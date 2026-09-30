package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;

/** Flat rounded button: hover animation, staggered entrance, toggle switch, animated gear icon. */
public class UiButton extends GuiButton {
    public static final int NORMAL = 0, PRIMARY = 1, DANGER = 2, TAB = 3, TOGGLE = 4;
    public static final int ICON_NONE = 0, ICON_GEAR = 1;

    public int style = NORMAL;
    public int icon = ICON_NONE;
    public boolean selected;
    public boolean on;
    /** entrance delay in ms */
    public long delay;

    private float hover, knob, spin;
    private final long born = System.currentTimeMillis();
    private long last = System.nanoTime();

    public UiButton(int id, int x, int y, int w, int h, String text) {
        super(id, x, y, w, h, text);
    }

    public UiButton style(int s) { this.style = s; return this; }
    public UiButton icon(int i) { this.icon = i; return this; }
    public UiButton delay(long d) { this.delay = d; return this; }

    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition
                && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;

        long nowN = System.nanoTime();
        float dt = Math.min(0.1f, (nowN - last) / 1.0e9f);
        last = nowN;
        hover += (((this.hovered && this.enabled) ? 1f : 0f) - hover) * Math.min(1f, dt * 14f);
        knob += ((on ? 1f : 0f) - knob) * Math.min(1f, dt * 16f);
        spin = (spin + dt * (40f + 380f * hover)) % 360f;

        float ap = Fade.ease((System.currentTimeMillis() - born - delay) / 320f);
        if (ap <= 0.01f) return;

        int x = xPosition, y = yPosition + (int) ((1f - ap) * 8f), w = width, h = height;
        int fill, border, text;
        switch (style) {
            case PRIMARY:
                fill = Draw.lerp(Theme.ACCENT_DK, 0xFF0891B2, hover);
                border = Draw.lerp(0xFF0891B2, Theme.ACCENT, hover);
                text = Theme.TEXT;
                break;
            case DANGER:
                fill = Draw.lerp(0xFF2A1218, 0xFF5B1A22, hover);
                border = Draw.lerp(0xFF4A1D25, Theme.BAD, hover);
                text = Draw.lerp(0xFFFCA5A5, Theme.TEXT, hover);
                break;
            case TAB:
                fill = selected ? Theme.PANEL2 : Draw.lerp(Theme.BG1, Theme.PANEL, hover);
                border = selected ? Theme.BORDER_HI : Draw.lerp(Theme.BG1, Theme.BORDER, hover);
                text = selected ? Theme.ACCENT : Draw.lerp(Theme.MUTED, Theme.TEXT, hover);
                break;
            default:
                fill = Draw.lerp(Theme.PANEL2, Theme.PANEL3, hover);
                border = Draw.lerp(Theme.BORDER, Theme.ACCENT, hover);
                text = Draw.lerp(Theme.SOFT, Theme.TEXT, hover);
        }
        if (!enabled) { fill = Theme.PANEL; border = Theme.BORDER; text = Theme.DIM; }

        Draw.blend();
        Draw.panel(x, y, w, h, 4, Draw.fade(fill, ap), Draw.fade(border, ap));
        if (style == TAB && selected) Draw.roundRect(x + 6, y + h - 2, w - 12, 2, 1, Draw.fade(Theme.ACCENT, ap));

        int tc = Draw.fade(text, ap);
        if (style == TOGGLE) {
            Draw.text(displayString, x + 8, y + (h - 8) / 2f, tc, 1f, false);
            int sw = 24, sh = 10, sx = x + w - 8 - sw, sy = y + (h - sh) / 2;
            Draw.roundRect(sx, sy, sw, sh, 5, Draw.fade(Draw.lerp(Theme.PANEL3, Theme.ACCENT_DK, knob), ap));
            int kx = sx + 1 + (int) ((sw - sh) * knob);
            Draw.roundRect(kx, sy + 1, sh - 2, sh - 2, 4, Draw.fade(Draw.lerp(Theme.MUTED, Theme.ACCENT, knob), ap));
        } else if (icon == ICON_GEAR) {
            int tw = Draw.width(displayString, 1f);
            float startX = x + (w - (tw + 18)) / 2f;
            float cy = y + h / 2f;
            Draw.gear(startX + 6f, cy, 5.5f, spin, Draw.fade(Draw.lerp(Theme.MUTED, Theme.ACCENT, hover), ap), Draw.fade(fill, ap));
            Draw.text(displayString, startX + 18f, y + (h - 8) / 2f, tc, 1f, true);
        } else {
            Draw.centered(displayString, x + w / 2f, y + (h - 8) / 2f, tc, 1f, style != TAB);
        }
    }
}
