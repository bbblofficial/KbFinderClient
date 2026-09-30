package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import java.awt.Color;
import java.io.IOException;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiMultiplayer;
import net.minecraft.client.gui.GuiOptions;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.GuiSelectWorld;

public class GuiModernMenu extends GuiScreen {
    private final KBTracker tracker;
    private final long opened = System.currentTimeMillis();
    private int panelX, panelY, panelW, panelH;

    public GuiModernMenu(KBTracker tracker) {
        this.tracker = tracker;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        int bw = 190, bh = 22, gap = 6;
        int cx = this.width / 2;
        int total = 5 * bh + 4 * gap;
        int top = this.height / 2 - total / 2 + 22;
        panelW = bw + 28;
        panelH = total + 28;
        panelX = cx - panelW / 2;
        panelY = top - 14;

        String[] names = { "Singleplayer", "Multiplayer", "Knockback Analyzer", "Options", "Quit Game" };
        for (int i = 0; i < 5; i++) {
            UiButton b = new UiButton(i + 1, cx - bw / 2, top + i * (bh + gap), bw, bh, names[i]);
            if (i == 2) b.style = UiButton.PRIMARY;
            if (i == 4) b.style = UiButton.DANGER;
            this.buttonList.add(b);
        }
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: this.mc.displayGuiScreen(new GuiSelectWorld(this)); break;
            case 2: this.mc.displayGuiScreen(new GuiMultiplayer(this)); break;
            case 3: this.mc.displayGuiScreen(new GuiAnalyzer(tracker, this)); break;
            case 4: this.mc.displayGuiScreen(new GuiOptions(this, this.mc.gameSettings)); break;
            case 5: this.mc.shutdown(); break;
            default: break;
        }
    }

    @Override
    protected void keyTyped(char c, int key) throws IOException {
        // main menu cannot be closed with ESC
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        this.drawGradientRect(0, 0, this.width, this.height, Theme.BG0, Theme.BG1);
        Draw.particles(this.width, this.height, 70, 0x22D3EE, 0.35f);
        Draw.particles(this.width, this.height, 25, 0xA78BFA, 0.30f);

        int cx = this.width / 2;
        float t = (System.currentTimeMillis() % 100000L) / 1000f;

        // title
        String title = "ORYVEX";
        float sc = 4f;
        float tx = cx - fontRendererObj.getStringWidth(title) * sc / 2f;
        int ty = Math.max(10, panelY - 66);
        for (int i = 0; i < title.length(); i++) {
            String ch = title.substring(i, i + 1);
            float hue = 0.50f + 0.17f * (0.5f + 0.5f * (float) Math.sin(t * 0.9f + i * 0.6f));
            int col = Color.HSBtoRGB(hue, 0.55f, 1f) | 0xFF000000;
            Draw.text(ch, tx, ty, col, sc, true);
            tx += fontRendererObj.getStringWidth(ch) * sc;
        }
        String sub = "K N O C K B A C K   C L I E N T";
        Draw.centered(sub, cx, ty + 38, Theme.MUTED, 0.9f, false);
        Draw.rect(cx - 30, ty + 52, 60, 1, Theme.ACCENT_DK);

        // button panel
        Draw.panel(panelX, panelY, panelW, panelH, 8, 0xF00C121D, Theme.BORDER);

        // live profile pill
        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Last profile   " + p.summary() + "   (" + p.used + " hits)";
            int w = Draw.width(s, 0.85f) + 20;
            int py = panelY + panelH + 10;
            Draw.panel(cx - w / 2, py, w, 15, 7, Theme.PANEL, Theme.BORDER);
            Draw.centered(s, cx, py + 4, Theme.SOFT, 0.85f, false);
        }

        Draw.text("KB Client " + "2.0", 6, this.height - 12, Theme.DIM, 0.8f, false);
        Draw.right("Forge 1.8.9", this.width - 6, this.height - 12, Theme.DIM, 0.8f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);

        float k = 1f - Draw.clamp((System.currentTimeMillis() - opened) / 500f);
        if (k > 0f) Gui.drawRect(0, 0, this.width, this.height, ((int) (k * 255f)) << 24);
    }
}
