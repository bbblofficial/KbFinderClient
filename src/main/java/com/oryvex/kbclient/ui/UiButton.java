package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import org.lwjgl.input.Mouse;

/**
 * Modern flat button with:
 *  - Correct icon sizing (never exceeds button height)
 *  - Smooth hover / press / toggle animations
 *  - Staggered intro animation
 *  - Multiple styles: NORMAL, PRIMARY, DANGER, TAB, TOGGLE, GHOST
 */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public static final int GHOST   = 5;

    public int style = NORMAL;
    public int icon = Draw.ICON_NONE;
    public boolean selected;
    public boolean on;
    public long delay;
    public boolean left;
    public float textSize = Theme.T_MD;

    private final Anim hover = new Anim(), press = new Anim(), knob = new Anim();
    private final long born = System.currentTimeMillis();
    private long lastNs = System.nanoTime();
    private float spin;

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

        long nowN = System.nanoTime();
        float dt = Math.min(0.1f, (nowN - lastNs) / 1.0e9f);
        lastNs = nowN;

        boolean act = this.hovered && this.enabled;
        float hv = hover.to(act ? 1f : 0f, 18f);
        float pr = press.to(act && Mouse.isButtonDown(0) ? 1f : 0f, 34f);
        float kn = knob.to(on ? 1f : 0f, 20f);
        spin = (spin + dt * (28f + 260f * hv)) % 360f;

        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 360f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.55f;

        // press feedback: shift down 1px and reduce height 1px
        float x = xPosition + pr * 0.5f;
        float y = yPosition + pr * 0.5f + (1f - ap) * 8f;
        float w = width - pr;
        float h = height - pr;
        float r = Math.min(h / 2f, style == TAB ? 4f : 6f);
        float cy = y + h / 2f;

        int accent  = Theme.accent();
        int accent2 = Theme.accent2();
        int textCol;

        switch (style) {
            case PRIMARY: {
                int c1 = Draw.lerp(Draw.shade(accent, 0.75f), accent, hv);
                int c2 = Draw.lerp(Draw.shade(accent2, 0.75f), accent2, hv);
                Draw.roundRect(x, y, w, h, r, Draw.fade(c1, ap));
                Draw.roundRect(x, y + h * 0.4f, w, h * 0.6f, r, Draw.fade(c2, ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(0x33FFFFFF, ap));
                textCol = 0xFFFFFFFF;
                break;
            }
            case DANGER: {
                int fill = Draw.lerp(0x22FB7185, 0x55FB7185, hv);
                Draw.roundRect(x, y, w, h, r, Draw.fade(fill, ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(0x44FB7185, 0xFFFB7185, hv), ap));
                textCol = Draw.lerp(0xFFFCA5A5, 0xFFFFFFFF, hv);
                break;
            }
            case TAB: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(selected ? Theme.FILL_HI : Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            case TOGGLE: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv * 0.7f), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.5f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, Math.max(hv, kn * 0.5f));
                break;
            }
            case GHOST: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            default: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.65f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
            }
        }

        textCol = Draw.fade(textCol, ap);

        if (style == TOGGLE) {
            // label on left, switch on right
            float sw = 22f, sh = 12f;
            float sx = x + w - sw - 10f;
            Draw.left(Draw.fit(displayString, w - sw - 26f, textSize, false),
                    x + 10f, cy, textCol, textSize, false);
            drawToggleSwitch(sx, cy - sh / 2f, sw, sh, kn, ap);
            return;
        }

        // ---- icon sizing: icon diameter = min(button height * 0.55, 12) ----
        boolean hasIcon = icon != Draw.ICON_NONE;
        float iconSize = Math.min(h * 0.55f, 12f);
        float gap = 6f;

        String label = Draw.fit(displayString,
                w - (hasIcon ? iconSize + gap + 20f : 20f), textSize, false);
        float tw = Draw.w(label, textSize, false);

        float contentW = hasIcon ? iconSize + gap + tw : tw;
        float startX;
        if (left) startX = x + 12f;
        else      startX = x + (w - contentW) / 2f;

        if (hasIcon) {
            float icx = startX + iconSize / 2f;
            int ic = (style == PRIMARY) ? textCol
                    : Draw.fade(Draw.lerp(Theme.SOFT, accent, hv), ap);
            if (style == DANGER) ic = textCol;
            Draw.icon(icon, icx, cy, iconSize, ic);
            startX += iconSize + gap;
        }

        if (left) {
            Draw.left(label, startX, cy, textCol, textSize, style == PRIMARY);
        } else {
            Draw.left(label, startX, cy, textCol, textSize, style == PRIMARY);
        }

        if (style == TAB && selected) {
            Draw.roundRect(x + 8f, y + h - 2f, w - 16f, 2f, 1f, Draw.fade(accent, ap));
        }
    }

    private void drawToggleSwitch(float sx, float sy, float sw, float sh, float knob, float ap) {
        int off = Draw.fade(0x30FFFFFF, ap);
        int onC = Draw.fade(Theme.accent(), ap);
        int track = Draw.lerp(off, onC, knob);
        Draw.roundRect(sx, sy, sw, sh, sh / 2f, track);
        float kx = sx + sh / 2f + (sw - sh) * knob;
        Draw.circle(kx, sy + sh / 2f, sh / 2f - 1.5f, Draw.fade(0xFFFFFFFF, ap));
    }
}
