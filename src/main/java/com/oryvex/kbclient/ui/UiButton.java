package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;

/** Flat, rounded, animated button. */
public class UiButton extends GuiButton {
    public static final int NORMAL = 0, PRIMARY = 1, DANGER = 2, TAB = 3;

    public int style = NORMAL;
    public boolean selected;
    private float hover;
    private long last = System.nanoTime();

    public UiButton(int id, int x, int y, int w, int h, String text) {
        super(id, x, y, w, h, text);
    }

    public UiButton style(int s) { this.style = s; return this; }

    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition
                && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;

        long now = System.nanoTime();
        float dt = Math.min(0.1f, (now - last) / 1.0e9f);
        last = now;
        float target = (this.hovered && this.enabled) ? 1f : 0f;
        hover += (target - hover) * Math.min(1f, dt * 14f);

        int x = xPosition, y = yPosition, w = width, h = height;
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

        Draw.panel(x, y, w, h, 4, fill, border);
        if (style == TAB && selected) Draw.roundRect(x + 6, y + h - 2, w - 12, 2, 1, Theme.ACCENT);
        Draw.centered(displayString, x + w / 2f, y + (h - 8) / 2f, text, 1f, style != TAB);
    }
}
