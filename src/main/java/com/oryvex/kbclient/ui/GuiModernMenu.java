package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBClientMod;
import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiMultiplayer;
import net.minecraft.client.gui.GuiSelectWorld;

public class GuiModernMenu extends FadeScreen {
    private final KBTracker tracker;
    private int sidebarW;

    public GuiModernMenu(KBTracker tracker) {
        this.tracker = tracker;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        sidebarW = 200;
        int bw = 160, bh = 24, gap = 8;
        int bx = 20; 
        int top = this.height / 2 - (6 * bh + 5 * gap) / 2 + 10;

        this.buttonList.add(new UiButton(1, bx, top, bw, bh, "Singleplayer").delay(100));
        this.buttonList.add(new UiButton(2, bx, top + (bh + gap), bw, bh, "Multiplayer").delay(150));
        this.buttonList.add(new UiButton(6, bx, top + 2 * (bh + gap), bw, bh, "Alt Manager").delay(200));
        this.buttonList.add(new UiButton(3, bx, top + 3 * (bh + gap), bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(250));
        this.buttonList.add(new UiButton(4, bx, top + 4 * (bh + gap), bw, bh, "Options").icon(UiButton.ICON_GEAR).delay(300));
        this.buttonList.add(new UiButton(5, bx, top + 5 * (bh + gap), bw, bh, "Quit").style(UiButton.DANGER).delay(350));
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: closeTo(new GuiSelectWorld(this)); break;
            case 2: closeTo(new GuiMultiplayer(this)); break;
            case 3: closeTo(new GuiAnalyzer(tracker, this)); break;
            case 4: closeTo(new GuiKbOptions(tracker, this)); break;
            case 6: closeTo(new GuiAltManager(this)); break;
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
        // Dark animated gradient background
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);
        
        // Premium Plexus Effect
        if (Settings.particles) {
            Draw.plexusBackground(this.width, this.height, 0.45f);
        }

        // Glass Sidebar
        Draw.shadow(0, 0, sidebarW, this.height, 0f, 0xFF000000, 20f);
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // Logo on sidebar
        Draw.text("K B   C L I E N T", 20, 35, Theme.TEXT, 1.4f, true);
        Draw.text("v" + KBClientMod.VERSION, 22, 52, Theme.ACCENT, 0.85f, false);
        Draw.rect(20, 70, sidebarW - 40, 1, Theme.BORDER);

        // Info Panel on the right (Rise Style Status)
        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Last Profile: " + p.summary() + " (" + p.used + " hits)";
            int w = Draw.width(s, 0.85f) + 24;
            int px = this.width - w - 20;
            int py = 20;
            Draw.shadow(px, py, w, 20, 6f, 0xFF000000, 8f);
            Draw.roundRect(px, py, w, 20, 6f, Theme.PANEL);
            Draw.roundRect(px, py, w, 20, 6f, Theme.BORDER);
            Draw.text(s, px + 12, py + 6.5f, Theme.SOFT, 0.85f, false);
            Draw.roundRect(px - 4, py + 6, 8, 8, 4f, Theme.GOOD); // Online dot
        }

        // Account Display Bottom Left
        String acc = "User: " + mc.getSession().getUsername();
        Draw.text(acc, 20, this.height - 20, Theme.MUTED, 0.85f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
