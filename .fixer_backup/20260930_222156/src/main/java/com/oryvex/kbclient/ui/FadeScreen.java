package com.oryvex.kbclient.ui;

import java.io.IOException;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.GuiScreen;
import org.lwjgl.input.Keyboard;

/** Base class for all KB Client screens: fades in on open, fades out on close. */
public abstract class FadeScreen extends GuiScreen {
    private final long openedAt = System.currentTimeMillis();
    private boolean closing;
    private long closeAt;
    private long closeDur;
    private Runnable after;

    public boolean isClosing() { return closing; }

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
            r.run();
        }
    }

    /** call as the LAST step of drawScreen */
    protected final void drawFade() {
        long ms = Fade.ms();
        if (ms <= 0) return;
        long now = System.currentTimeMillis();
        float a = 1f - Fade.ease((now - openedAt) / (float) ms);
        if (closing) a = Math.max(a, Fade.ease((now - closeAt) / (float) closeDur));
        if (a > 0.004f) Gui.drawRect(0, 0, this.width, this.height, ((int) (a * 255f)) << 24);
    }

    protected void drawBackdrop(int particleCount) {
        if (this.mc != null && this.mc.theWorld != null) {
            this.drawGradientRect(0, 0, this.width, this.height, 0xD0070A11, 0xE0111A2B);
        } else {
            this.drawGradientRect(0, 0, this.width, this.height, Theme.BG0, Theme.BG1);
        }
        if (Settings.particles && particleCount > 0) Draw.particles(this.width, this.height, particleCount, 0x22D3EE, 0.25f);
    }

    @Override
    protected void mouseClicked(int x, int y, int b) throws IOException {
        if (closing) return;
        super.mouseClicked(x, y, b);
    }

    @Override
    protected final void keyTyped(char c, int key) throws IOException {
        if (closing) return;
        onKey(c, key);
    }

    protected void onKey(char c, int key) throws IOException {
        if (key == Keyboard.KEY_ESCAPE) closeTo(null);
    }
}
