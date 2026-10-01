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

        // Responsive sidebar: 26% of width, clamped.
        sidebarW = Math.max(180, Math.min(300, (int) (this.width * 0.26f)));

        int padding = Math.max(12, sidebarW / 10);
        int bw = sidebarW - padding * 2;
        int bh = Math.max(20, Math.min(28, this.height / 22));
        int gap = Math.max(4, bh / 5);

        int totalHeight = 6 * bh + 5 * gap;
        int top = Math.max(72, (this.height - totalHeight) / 2 + 10);

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
                    @Override public void run() { mc.shutdown(); }
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
        // Background
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);

        // Sidebar panel
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // -------- Title -------------------------------------------------
        String title = "ORYVEX";
        float titleScale = Math.max(1.4f, Math.min(2.2f, sidebarW / 130f));
        float titleW = Draw.font().getStringWidth(title) * titleScale;
        float titleY = Math.max(24f, this.height * 0.09f);
        Draw.text(title, (sidebarW - titleW) / 2f, titleY, Theme.TEXT, titleScale, true);

        String sub = "KB Client v" + KBClientMod.VERSION;
        float subScale = 0.85f;
        float subW = Draw.font().getStringWidth(sub) * subScale;
        Draw.text(sub, (sidebarW - subW) / 2f, titleY + 26, Theme.ACCENT, subScale, false);

        Draw.rect(20, titleY + 44, sidebarW - 40, 1, Theme.BORDER);

        // -------- Profile widget (top-right) ----------------------------
        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Profile:  " + p.summary();
            int w = Draw.width(s, 0.85f) + 34;
            int px = this.width - w - 14;
            int py = 14;
            if (px > sidebarW + 8) {
                Draw.roundRect(px, py, w, 22, 6f, Theme.PANEL2);
                Draw.roundOutline(px, py, w, 22, 6f, 1f, Theme.BORDER);
                Draw.roundRect(px + 9, py + 8, 6, 6, 3f, Theme.GOOD);
                Draw.text(s, px + 22, py + 7, Theme.TEXT, 0.85f, false);
            }
        }

        // -------- User card (bottom) -----------------------------------
        int userY = this.height - Math.max(34, 40);
        Draw.rect(20, userY - 12, sidebarW - 40, 1, Theme.BORDER);

        Draw.roundRect(20, userY - 2, 20, 20, 10f, Theme.PANEL3);
        Draw.centered("L", 30, userY + 4, Theme.SOFT, 1.0f, false);

        Draw.text("Logged in as", 46, userY, Theme.MUTED, 0.75f, false);
        String name = mc.getSession().getUsername();
        int nameMax = sidebarW - 56;
        String nameF = Draw.fit(name, nameMax, 0.95f, false);
        Draw.text(nameF, 46, userY + 10, Theme.TEXT, 0.95f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
