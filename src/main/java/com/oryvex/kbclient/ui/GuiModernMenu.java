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
        
        // FULLY RESPONSIVE CALCULATION
        sidebarW = Math.max(220, Math.min(300, this.width / 4)); // Adapts to screen width perfectly
        int padding = 24;
        int bw = sidebarW - (padding * 2); 
        int bh = 28, gap = 8;
        
        // Vertically center the buttons exactly
        int totalHeight = (6 * bh) + (5 * gap);
        int top = (this.height - totalHeight) / 2 + 10;

        this.buttonList.add(new UiButton(1, padding, top, bw, bh, "Singleplayer").delay(100));
        this.buttonList.add(new UiButton(2, padding, top + (bh + gap), bw, bh, "Multiplayer").delay(150));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap), bw, bh, "Alt Manager").delay(200));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap), bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(250));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap), bw, bh, "Options").icon(UiButton.ICON_GEAR).delay(300));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap), bw, bh, "Quit").style(UiButton.DANGER).delay(350));
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
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);
        
        if (Settings.particles) {
            Draw.plexusBackground(this.width, this.height, 0.65f); // Beautiful dense plexus
        }

        // Sidebar Background
        Draw.shadow(0, 0, sidebarW, this.height, 0f, 0xFF000000, 30f);
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // Perfect Typography Logo
        String title = "ORYVEX";
        float scale = 2.2f;
        float titleW = Draw.font().getStringWidth(title) * scale;
        Draw.text(title, (sidebarW - titleW) / 2f, 40, Theme.TEXT, scale, true);
        
        String sub = "KB Client v" + KBClientMod.VERSION;
        float subW = Draw.font().getStringWidth(sub) * 0.9f;
        Draw.text(sub, (sidebarW - subW) / 2f, 65, Theme.ACCENT, 0.9f, false);
        
        Draw.rect(30, 85, sidebarW - 60, 1, Theme.BORDER);

        // Premium Floating Widget
        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Profile: " + p.summary();
            int w = Draw.width(s, 0.85f) + 36;
            int px = this.width - w - 20;
            int py = 20;
            Draw.shadow(px, py, w, 24, 6f, 0xFF000000, 12f);
            Draw.roundRect(px, py, w, 24, 6f, Theme.PANEL2);
            Draw.roundRect(px, py, w, 24, 6f, Theme.BORDER);
            
            Draw.roundRect(px + 10, py + 9, 6, 6, 3f, Theme.GOOD);
            Draw.shadow(px + 10, py + 9, 6, 6, 3f, Theme.GOOD, 5f);
            Draw.text(s, px + 24, py + 8.5f, Theme.TEXT, 0.85f, false);
        }

        // Improved User Card
        int userY = this.height - 45;
        Draw.rect(30, userY - 15, sidebarW - 60, 1, Theme.BORDER);
        
        // Avatar Circle Placeholder
        Draw.roundRect(24, userY - 3, 22, 22, 11f, Theme.PANEL3); 
        Draw.text("L", 32, userY + 4, Theme.SOFT, 1.0f, false);
        
        Draw.text("Logged in as", 56, userY, Theme.MUTED, 0.75f, false);
        String name = mc.getSession().getUsername();
        
        // Truncate name if too long
        if (Draw.font().getStringWidth(name) > (sidebarW - 70)) {
            name = name.substring(0, 10) + "...";
        }
        Draw.text(name, 56, userY + 9, Theme.TEXT, 0.95f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
