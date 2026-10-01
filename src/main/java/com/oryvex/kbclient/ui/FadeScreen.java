package com.oryvex.kbclient.ui;

import java.io.IOException;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.GuiScreen;
import org.lwjgl.input.Keyboard;
import org.lwjgl.input.Mouse;

/** Base class for all KB Client screens: fades in on open, fades out on close, animated backdrop. */
public abstract class FadeScreen extends GuiScreen {
    private long openedAt = System.currentTimeMillis();
    private boolean closing;
    private long closeAt;
    private long closeDur;
    private Runnable after;
    private boolean finished;
    public boolean isClosing() { return closing; }
    /** Called every time this screen is displayed (also when a parent screen is re-opened via Back). */
    @Override
    public void setWorldAndResolution(Minecraft mc, int width, int height) {
        if (finished) {          // was closed earlier -> start fresh (no black overlay, input enabled)
            closing = false;
            finished = false;
            after = null;
            openedAt = System.currentTimeMillis();
        }
        super.setWorldAndResolution(mc, width, height);
    }
    public void closeTo(final GuiScreen next) {
        closeThen(new Runnable() {
            @Override
            public void run() { Minecraft.getMinecraft().displayGuiScreen(next); }
        });
    }
    public void closeThen(Runnable r) {
        if (closing) return;
        long ms = Fade.ms();
        if (ms <= 0) { r.run(); return; }
        closing = true;
        closeAt = System.currentTimeMillis();
        closeDur = ms;
        after = r;
    }
    @Override
    public void updateScreen() {
        super.updateScreen();
        if (closing && after != null && System.currentTimeMillis() - closeAt >= closeDur) {
            Runnable r = after;
            after = null;
            finished = true;
            r.run();
        }
    }
    /** 0..1 eased "how open is this screen" - use it to scale / fade panels in and out */
    protected final float openAnim() {
        long ms = Fade.ms();
        long now = System.currentTimeMillis();
        float a = ms <= 0 ? 1f : Draw.easeOut((now - openedAt) / (float) (ms + 120));
        if (closing) a = Math.min(a, 1f - Draw.ease((now - closeAt) / (float) closeDur));
        return a;
    }
    /** call as the LAST step of drawScreen */
    protected final void drawFade() {
        long ms = Fade.ms();
        if (ms <= 0) return;
        long now = System.currentTimeMillis();
        float a = 1f - Fade.ease((now - openedAt) / (float) ms);
        if (closing) a = Math.max(a, Fade.ease((now - closeAt) / (float) closeDur));
        if (a > 0.004f) Gui.drawRect(0, 0, this.width, this.height, ((int) (a * 255f)) << 24);
        Draw.resetColor();
    }
    protected void drawBackdrop(int mx, int my) {
        Background.draw(this.width, this.height, mx, my, this.mc != null && this.mc.theWorld != null, 1f);
    }
    @Override
    protected void mouseClicked(int x, int y, int b) throws IOException {
        if (closing) return;
        super.mouseClicked(x, y, b);
    }
    @Override
    public void handleMouseInput() throws IOException {
        super.handleMouseInput();
        int d = Mouse.getEventDWheel();
        if (d != 0 && !closing) onScroll(d > 0 ? -1 : 1);
    }
    /** mouse wheel: -1 = up, +1 = down */
    protected void onScroll(int dir) { }
    @Override
    protected final void keyTyped(char c, int key) throws IOException {
        if (closing) return;
        onKey(c, key);
    }
    protected void onKey(char c, int key) throws IOException {
        if (key == Keyboard.KEY_ESCAPE) closeTo(null);
    }
}
