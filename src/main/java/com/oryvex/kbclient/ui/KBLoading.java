package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.LoadingScreenRenderer;
import net.minecraft.client.gui.ScaledResolution;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.shader.Framebuffer;

/** Replaces Minecraft's loading renderer (world load / save / chunk generation). */
public class KBLoading extends LoadingScreenRenderer {
    private final Minecraft mcRef;
    private String title = "";
    private String sub = "";
    private int progress = -1;
    private long startedAt;
    private long lastFrame;
    private Framebuffer fb;

    public KBLoading(Minecraft mc) {
        super(mc);
        this.mcRef = mc;
    }

    private void begin(String t) {
        long now = System.currentTimeMillis();
        if (now - lastFrame > 1500L) startedAt = now;
        title = t == null ? "" : t;
        sub = "";
        progress = -1;
    }

    @Override
    public void resetProgressAndMessage(String message) {
        if (!Settings.customLoading) { super.resetProgressAndMessage(message); return; }
        begin(message);
        frame();
    }

    @Override
    public void displaySavingString(String message) {
        if (!Settings.customLoading) { super.displaySavingString(message); return; }
        begin(message);
        frame();
    }

    @Override
    public void displayLoadingString(String message) {
        if (!Settings.customLoading) { super.displayLoadingString(message); return; }
        if (System.currentTimeMillis() - lastFrame > 1500L) begin("");
        sub = message == null ? "" : message;
        progress = -1;
        // the integrated server start-up loop only calls us every ~200 ms: animate in between
        long end = System.currentTimeMillis() + 120L;
        do { frame(); } while (System.currentTimeMillis() < end);
    }

    @Override
    public void setLoadingProgress(int p) {
        if (!Settings.customLoading) { super.setLoadingProgress(p); return; }
        progress = p;
        if (System.currentTimeMillis() - lastFrame >= 30L) frame();
    }

    @Override
    public void setDoneWorking() {
        if (!Settings.customLoading) super.setDoneWorking();
    }

    private void frame() {
        try {
            Minecraft mc = mcRef;
            ScaledResolution sr = new ScaledResolution(mc);
            int k = sr.getScaleFactor(), w = sr.getScaledWidth(), h = sr.getScaledHeight();
            if (fb == null || fb.framebufferWidth != w * k || fb.framebufferHeight != h * k) {
                if (fb != null) fb.deleteFramebuffer();
                fb = new Framebuffer(w * k, h * k, true);
            }
            fb.bindFramebuffer(false);
            GlStateManager.matrixMode(5889);
            GlStateManager.loadIdentity();
            GlStateManager.ortho(0.0D, sr.getScaledWidth_double(), sr.getScaledHeight_double(), 0.0D, 100.0D, 300.0D);
            GlStateManager.matrixMode(5888);
            GlStateManager.loadIdentity();
            GlStateManager.translate(0.0F, 0.0F, -200.0F);
            GlStateManager.clear(256);
            GlStateManager.disableLighting();
            GlStateManager.disableFog();
            GlStateManager.enableTexture2D();

            LoadingArt.draw(w, h, title, sub, progress);

            long ms = Fade.ms();
            if (ms > 0) {
                float a = 1f - Fade.ease((System.currentTimeMillis() - startedAt) / (float) ms);
                if (a > 0.004f) Gui.drawRect(0, 0, w, h, ((int) (a * 255f)) << 24);
            }

            fb.unbindFramebuffer();
            fb.framebufferRender(w * k, h * k);
            GlStateManager.enableAlpha();
            GlStateManager.alphaFunc(516, 0.1F);
            mc.updateDisplay();
            lastFrame = System.currentTimeMillis();
        } catch (Throwable ignored) { }
    }
}
