package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import org.lwjgl.input.Mouse;

public class UiButton extends GuiButton {
    public static final int NORMAL = 0, PRIMARY = 1, DANGER = 2, TAB = 3, TOGGLE = 4, GHOST = 5;
    public static final int ICON_NONE = Draw.ICON_NONE, ICON_GEAR = Draw.ICON_GEAR;

    public int style = NORMAL;
    public int icon = ICON_NONE;
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

        float inset = pr * 0.9f;
        float x = xPosition + inset;
        float y = yPosition + inset + (1f - ap) * 7f;
        float w = width - inset * 2f;
        float h = height - inset * 2f;
        float r = Math.min(h / 2f, style == TAB ? 4f : 7f);
        float cy = y + h / 2f;

        int accent = Theme.accent();
        int accent2 = Theme.accent2();
        int textCol;

        switch (style) {
            case PRIMARY: {
                int c1 = Draw.lerp(Draw.shade(accent, 0.86f), accent, hv);
                int c2 = Draw.lerp(Draw.shade(accent2, 0.86f), accent2, hv);
                Draw.roundRect(x, y, w, h, r, Draw.fade(c1, ap));
                Draw.roundOutline(x, y, w, h, r, 1f, Draw.fade(0x55FFFFFF, ap * (0.5f + 0.5f * hv)));
                textCol = Ui.onAccent();
                break;
            }
            case DANGER: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, 0x55FB7185, hv), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Theme.BAD, hv), ap));
                textCol = Draw.lerp(Draw.lerp(Theme.SOFT, Theme.BAD, 0.4f), 0xFFFFFFFF, hv * 0.6f);
                break;
            }
            case TAB: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(selected ? Theme.FILL : Draw.lerp(0x00FFFFFF, Theme.FILL, hv), ap));
                textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv);
                break;
            }
            case TOGGLE: {
                Draw.roundRect(x, y, w, h, r,
                        Draw.fade(Draw.lerp(Theme.FILL, Theme.FILL_HI, hv * 0.8f), ap));
                Draw.roundOutline(x, y, w, h, r, 1f,
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.7f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, Math.max(hv, kn * 0.7f));
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
                        Draw.fade(Draw.lerp(Theme.STROKE, Draw.alpha(accent, 0.75f), hv), ap));
                textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
            }
        }

        textCol = Draw.fade(textCol, ap);

        if (style == TOGGLE) {
            Draw.left(Draw.fit(displayString, w - 48f, textSize, false), x + 10f, cy, textCol, textSize, false);
            Ui.toggle(x + w - 10f - 24f, cy, kn, ap);
            return;
        }

        float isz = Math.min(11f, h - 8f);
        boolean hasIcon = icon != ICON_NONE;
        String label = Draw.fit(displayString, w - (hasIcon ? isz + 22f : 16f), textSize, false);
        float tw = Draw.w(label, textSize, false);
        float startX;
        if (left) startX = x + 12f;
        else      startX = x + (w - (tw + (hasIcon ? isz + 6f : 0f))) / 2f;

        if (hasIcon) {
            float ix = startX + isz / 2f;
            int ic = style == PRIMARY ? textCol
                    : Draw.fade(Draw.lerp(Draw.lerp(Theme.MUTED, Theme.SOFT, 0.5f),
                            Draw.lerp(accent, 0xFFFFFFFF, 0.25f), hv), ap);
            if (style == DANGER) ic = Draw.fade(Draw.lerp(Theme.BAD, 0xFFFFFFFF, hv * 0.5f), ap);
            if (icon == ICON_GEAR) Draw.gear(ix, cy, isz * 1.15f, spin, ic);
            else Draw.icon(icon, ix, cy, isz * 1.15f, ic);
            startX += isz + 6f;
        }

        if (left) {
            Draw.left(label, startX, cy, textCol, textSize, style == PRIMARY);
        } else {
            Draw.centered(label, x + w / 2f, cy, textCol, textSize, style == PRIMARY);
        }

        if (style == TAB && selected) {
            Draw.roundRect(x + 8f, y + h - 2f, w - 16f, 2f, 1f, Draw.fade(accent, ap));
        }
    }
}
