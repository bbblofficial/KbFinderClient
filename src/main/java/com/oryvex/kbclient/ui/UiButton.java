package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.renderer.GlStateManager;

public class UiButton extends GuiButton {
    public static final int NORMAL = 0, PRIMARY = 1, DANGER = 2, TAB = 3, TOGGLE = 4;
    public static final int ICON_NONE = 0, ICON_GEAR = 1;

    public int style = NORMAL;
    public int icon = ICON_NONE;
    public boolean selected;
    public boolean on;
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
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;

        long nowN = System.nanoTime();
        float dt = Math.min(0.1f, (nowN - last) / 1.0e9f);
        last = nowN;
        hover += (((this.hovered && this.enabled) ? 1f : 0f) - hover) * Math.min(1f, dt * 18f);
        knob += ((on ? 1f : 0f) - knob) * Math.min(1f, dt * 20f);
        spin = (spin + dt * (40f + 380f * hover)) % 360f;

        float ap = Fade.ease((System.currentTimeMillis() - born - delay) / 320f);
        if (ap <= 0.01f) return;

        int fill, text;
        switch (style) {
            case PRIMARY:
                fill = Draw.lerp(Theme.ACCENT_DK, Theme.ACCENT, hover);
                text = Theme.TEXT;
                break;
            case DANGER:
                fill = Draw.lerp(0xAA7F1D1D, Theme.BAD, hover);
                text = Theme.TEXT;
                break;
            case TAB:
                fill = selected ? Theme.PANEL2 : Draw.lerp(0x00000000, Theme.PANEL, hover);
                text = selected ? Theme.ACCENT : Draw.lerp(Theme.MUTED, Theme.TEXT, hover);
                break;
            default:
                fill = Draw.lerp(Theme.PANEL, Theme.PANEL2, hover);
                text = Draw.lerp(Theme.SOFT, Theme.TEXT, hover);
        }
        if (!enabled) { fill = Theme.PANEL; text = Theme.DIM; }

        Draw.blend();
        
        // Matrix Scale Animation (The "Rise" button pop effect)
        float scale = 1.0f + (hover * 0.04f); // Expands 4%
        float cx = xPosition + width / 2f;
        float cy = yPosition + height / 2f;
        
        GlStateManager.pushMatrix();
        GlStateManager.translate(cx, cy, 0);
        GlStateManager.scale(scale, scale, 1f);
        GlStateManager.translate(-cx, -cy, 0);

        int y = yPosition + (int) ((1f - ap) * 8f);
        
        if(style != TAB) Draw.shadow(xPosition, y, width, height, 4f, Draw.fade(fill, ap * 0.8f), 6f);
        Draw.roundRect(xPosition, y, width, height, 4f, Draw.fade(fill, ap));
        
        if (style == TAB && selected) Draw.roundRect(xPosition + 8, y + height - 2, width - 16, 2, 1f, Draw.fade(Theme.ACCENT, ap));

        int tc = Draw.fade(text, ap);
        if (style == TOGGLE) {
            Draw.text(displayString, xPosition + 8, y + (height - 8) / 2f, tc, 1f, false);
            int sw = 22, sh = 10, sx = xPosition + width - 8 - sw, sy = y + (height - sh) / 2;
            Draw.roundRect(sx, sy, sw, sh, 5f, Draw.fade(Draw.lerp(Theme.PANEL3, Theme.ACCENT_DK, knob), ap));
            Draw.roundRect(sx + 1 + (sw - sh) * knob, sy + 1, sh - 2, sh - 2, 4f, Draw.fade(Theme.TEXT, ap));
            if(knob > 0.1f) Draw.shadow(sx + 1 + (sw - sh) * knob, sy + 1, sh - 2, sh - 2, 4f, Draw.fade(Theme.ACCENT, ap * knob), 4f);
        } else if (icon == ICON_GEAR) {
            int tw = Draw.width(displayString, 1f);
            float startX = xPosition + (width - (tw + 18)) / 2f;
            Draw.gear(startX + 6f, y + height / 2f, 4.5f, spin, Draw.fade(Draw.lerp(Theme.MUTED, Theme.ACCENT, hover), ap), Draw.fade(fill, ap));
            Draw.text(displayString, startX + 18f, y + (height - 8) / 2f, tc, 1f, true);
        } else {
            Draw.centered(displayString, xPosition + width / 2f, y + (height - 8) / 2f, tc, 1f, style != TAB);
        }
        
        GlStateManager.popMatrix();
    }
}
