package com.oryvex.kbclient.ui;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
/** Simple flat button. No icons, no complex animations. */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public int style = NORMAL;
    public boolean selected;
    public boolean on;
    public long delay;
    private final Anim hover = new Anim();
    private final long born = System.currentTimeMillis();
    public UiButton(int id, int x, int y, int w, int h, String text) { super(id, x, y, w, h, text); }
    public UiButton style(int s) { this.style = s; return this; }
    public UiButton delay(long d) { this.delay = d; return this; }
    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;
        boolean act = this.hovered && this.enabled;
        float hv = hover.to(act ? 1f : 0f, 22f);
        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 260f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.5f;
        float x = xPosition;
        float y = yPosition + (1f - ap) * 6f;
        float w = width;
        float h = height;
        float r = 4f;
        float cy = y + h / 2f;
        int bg, border, textCol;
        switch (style) {
            case PRIMARY: bg = Draw.lerp(Theme.ACCENT_DK, Theme.ACCENT, hv); border = Theme.ACCENT; textCol = 0xFFFFFFFF; break;
            case DANGER: bg = Draw.lerp(0x18FB7185, 0x40FB7185, hv); border = Draw.lerp(0x44FB7185, Theme.BAD, hv); textCol = Draw.lerp(0xFFFCA5A5, 0xFFFFFFFF, hv); break;
            case TAB: bg = selected ? Theme.SURFACE2 : Draw.lerp(0x00FFFFFF, Theme.SURFACE2, hv); border = selected ? Theme.BORDER_HI : Theme.BORDER; textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv); break;
            case TOGGLE: bg = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv); border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv); textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv); break;
            default: bg = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv); border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv); textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
        }
        bg = Draw.fade(bg, ap);
        border = Draw.fade(border, ap);
        textCol = Draw.fade(textCol, ap);
        Draw.panel(x, y, w, h, r, bg, border);
        if (style == TOGGLE) {
            Draw.left(displayString, x + 8f, cy, textCol, 1.0f, false);
            float sw = 22f, sh = 12f;
            float sx = x + w - sw - 8f;
            int track = on ? Theme.ACCENT : 0x30FFFFFF;
            Draw.roundRect(sx, cy - sh/2, sw, sh, sh/2, Draw.fade(track, ap));
            float kx = sx + sh/2 + (sw - sh) * (on ? 1f : 0f);
            Draw.roundRect(kx - sh/2 + 1, cy - sh/2 + 1, sh-2, sh-2, sh/2-1, Draw.fade(0xFFFFFFFF, ap));
            return;
        }
        Draw.centered(displayString, x + w / 2f, cy, textCol, 1.0f, false);
        if (style == TAB && selected) Draw.rect(x + 4f, y + h - 2f, w - 8f, 2f, Theme.ACCENT);
    }
}