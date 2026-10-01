package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;

/** Simple flat button. No glow, no press animation. */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public static final int GHOST   = 5;

    // legacy aliases
    public static final int ICON_NONE = Draw.ICON_NONE;
    public static final int ICON_GEAR = Draw.ICON_GEAR;

    public int style = NORMAL;
    public int icon = Draw.ICON_NONE;
    public boolean selected;
    public boolean on;
    public long delay;
    public boolean left;
    public float textSize = Theme.T_MD;

    private final Anim hover = new Anim();
    private final long born = System.currentTimeMillis();

    public UiButton(int id, int x, int y, int w, int h, String text) {
        super(id, x, y, w, h, text);
    }

    public UiButton style(int s) { this.style = s; return this; }
    public UiButton icon(int i) { this.icon = i; return this; }
    public UiButton delay(long d) { this.delay = d; return this; }
    public UiButton left() { this.left = true; return this; }
    public UiButton size(float s) { this.textSize = s; return this; }

    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition
                && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;

        boolean act = this.hovered && this.enabled;
        float hv = hover.to(act ? 1f : 0f, 22f);
        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 260f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.5f;

        float x = xPosition;
        float y = yPosition + (1f - ap) * 6f;
        float w = width;
        float h = height;
        float r = 6f;
        float cy = y + h / 2f;

        int bg;
        int border;
        int textCol;

        switch (style) {
            case PRIMARY:
                bg     = Draw.lerp(Theme.ACCENT_DK, Theme.ACCENT, hv);
                border = Theme.ACCENT;
                textCol = 0xFFFFFFFF;
                break;
            case DANGER:
                bg     = Draw.lerp(0x18FB7185, 0x40FB7185, hv);
                border = Draw.lerp(0x44FB7185, Theme.BAD, hv);
                textCol = Draw.lerp(0xFFFCA5A5, 0xFFFFFFFF, hv);
                break;
            case TAB:
                bg     = selected ? Theme.SURFACE2 : Draw.lerp(0x00FFFFFF, Theme.SURFACE2, hv);
                border = selected ? Theme.BORDER_HI : Theme.BORDER;
                textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            case TOGGLE:
                bg     = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv);
                border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv);
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
                break;
            case GHOST:
                bg     = Draw.lerp(0x00FFFFFF, Theme.SURFACE2, hv);
                border = 0;
                textCol = Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            default:
                bg     = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv);
                border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv);
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
        }

        bg = Draw.fade(bg, ap);
        border = Draw.fade(border, ap);
        textCol = Draw.fade(textCol, ap);

        Draw.roundRect(x, y, w, h, r, bg);
        if (((border >>> 24) & 255) > 4) Draw.roundOutline(x, y, w, h, r, 1f, border);

        if (style == TOGGLE) {
            float sw = 22f, sh = 12f;
            float sx = x + w - sw - 10f;
            Draw.left(Draw.fit(displayString, w - sw - 26f, textSize, false),
                    x + 12f, cy, textCol, textSize, false);
            drawToggle(sx, cy - sh / 2f, sw, sh, Draw.lerp(0f, 1f,
                    (on ? 1f : 0f)), ap);
            return;
        }

        boolean hasIcon = icon != Draw.ICON_NONE;
        float iconSize = Math.min(h * 0.5f, 12f);
        float gap = 8f;
        String label = Draw.fit(displayString,
                w - (hasIcon ? iconSize + gap + 20f : 20f), textSize, false);
        float tw = Draw.w(label, textSize, false);
        float contentW = hasIcon ? iconSize + gap + tw : tw;
        float startX = left ? x + 12f : x + (w - contentW) / 2f;

        if (hasIcon) {
            float icx = startX + iconSize / 2f;
            Draw.icon(icon, icx, cy, iconSize, textCol);
            startX += iconSize + gap;
        }

        Draw.left(label, startX, cy, textCol, textSize, false);

        if (style == TAB && selected) {
            Draw.rect(x + 8f, y + h - 2f, w - 16f, 2f, Theme.ACCENT);
        }
    }

    private void drawToggle(float sx, float sy, float sw, float sh, float knob, float ap) {
        int track = on ? Theme.ACCENT : 0x30FFFFFF;
        Draw.roundRect(sx, sy, sw, sh, sh / 2f, Draw.fade(track, ap));
        float kx = sx + sh / 2f + (sw - sh) * knob;
        Draw.circle(kx, sy + sh / 2f, sh / 2f - 1.5f, Draw.fade(0xFFFFFFFF, ap));
    }
}