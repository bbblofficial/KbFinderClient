package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import java.awt.Color;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiMultiplayer;
import net.minecraft.client.gui.GuiSelectWorld;

public class GuiModernMenu extends FadeScreen {
    private final KBTracker tracker;
    private int panelX, panelY, panelW, panelH, titleY;

    public GuiModernMenu(KBTracker tracker) {
        this.tracker = tracker;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        int bw = 200, bh = 22, gap = 6, cx = this.width / 2;
        int rows = 4;
        int total = rows * bh + (rows - 1) * gap;
        int top = this.height / 2 - total / 2 + 26;
        panelW = bw + 28;
        panelH = total + 28;
        panelX = cx - panelW / 2;
        panelY = top - 14;
        titleY = Math.max(8, panelY - 72);

        int half = (bw - gap) / 2;
        this.buttonList.add(new UiButton(1, cx - bw / 2, top, bw, bh, "Singleplayer").delay(120));
        this.buttonList.add(new UiButton(2, cx - bw / 2, top + (bh + gap), bw, bh, "Multiplayer").delay(190));
        this.buttonList.add(new UiButton(3, cx - bw / 2, top + 2 * (bh + gap), bw, bh, "Knockback Analyzer").style(UiButton.PRIMARY).delay(260));
        this.buttonList.add(new UiButton(4, cx - bw / 2, top + 3 * (bh + gap), half, bh, "Options").icon(UiButton.ICON_GEAR).delay(330));
        this.buttonList.add(new UiButton(5, cx - bw / 2 + half + gap, top + 3 * (bh + gap), bw - half - gap, bh, "Quit").style(UiButton.DANGER).delay(400));
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: closeTo(new GuiSelectWorld(this)); break;
            case 2: closeTo(new GuiMultiplayer(this)); break;
            case 3: closeTo(new GuiAnalyzer(tracker, this)); break;
            case 4: closeTo(new GuiKbOptions(tracker, this)); break;
            case 5:
                closeThen(new Runnable() {
                    @Override
                    public void run() { mc.shutdown(); }
                });
                break;
            default: break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        // main menu cannot be closed with ESC
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        this.drawGradientRect(0, 0, this.width, this.height, Theme.BG0, Theme.BG1);
        if (Settings.particles) {
            Draw.particles(this.width, this.height, 70, 0x22D3EE, 0.35f);
            Draw.particles(this.width, this.height, 25, 0xA78BFA, 0.30f);
        }

        int cx = this.width / 2;
        float t = (System.currentTimeMillis() % 100000L) / 1000f;

        String title = "ORYVEX";
        float sc = 4f;
        float tx = cx - fontRendererObj.getStringWidth(title) * sc / 2f;
        for (int i = 0; i < title.length(); i++) {
            String ch = title.substring(i, i + 1);
            float hue = 0.50f + 0.17f * (0.5f + 0.5f * (float) Math.sin(t * 0.9f + i * 0.6f));
            int col = Color.HSBtoRGB(hue, 0.55f, 1f) | 0xFF000000;
            Draw.text(ch, tx, titleY, col, sc, true);
            tx += fontRendererObj.getStringWidth(ch) * sc;
        }
        Draw.centered("K N O C K B A C K   C L I E N T", cx, titleY + 38, Theme.MUTED, 0.9f, false);
        Draw.rect(cx - 30, titleY + 52, 60, 1, Theme.ACCENT_DK);

        Draw.panel(panelX, panelY, panelW, panelH, 8, Theme.GLASS, Theme.BORDER);

        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Last profile   " + p.summary() + "   (" + p.used + " hits)";
            int w = Draw.width(s, 0.85f) + 20;
            int py = panelY + panelH + 10;
            Draw.panel(cx - w / 2, py, w, 15, 7, Theme.PANEL, Theme.BORDER);
            Draw.centered(s, cx, py + 4, Theme.SOFT, 0.85f, false);
        }

        Draw.text("KB Client 3.0", 6, this.height - 12, Theme.DIM, 0.8f, false);
        Draw.right("Forge 1.8.9", this.width - 6, this.height - 12, Theme.DIM, 0.8f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
