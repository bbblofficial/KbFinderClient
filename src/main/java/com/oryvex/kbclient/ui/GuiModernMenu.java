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
        sidebarW = Math.max(180, Math.min(320, (int)(this.width * 0.28f)));

        int padding = Math.max(12, sidebarW / 10);
        int bw = sidebarW - padding * 2;
        int bh = Math.max(20, Math.min(28, this.height / 20));
        int gap = Math.max(4, bh / 6);

        int totalH = 6 * bh + 5 * gap;
        int top = Math.max(96, (this.height - totalH) / 2 + 20);

        this.buttonList.add(new UiButton(1, padding, top, bw, bh, "Singleplayer").delay(80));
        this.buttonList.add(new UiButton(2, padding, top + (bh + gap), bw, bh, "Multiplayer").delay(120));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap), bw, bh, "Alt Manager").delay(160));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap), bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(200));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap), bw, bh, "Options").icon(UiButton.ICON_GEAR).delay(240));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap), bw, bh, "Quit").style(UiButton.DANGER).delay(280));
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
                closeThen(new Runnable() { @Override public void run() { mc.shutdown(); } });
                break;
            default: break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        // main menu : ESC غیرفعال
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);

        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        float titleScale = Math.max(1.4f, Math.min(2.4f, sidebarW / 130f));
        String title = "ORYVEX";
        Draw.centered(title, sidebarW / 2f, 50f, Theme.TEXT, titleScale, true);

        float subScale = 0.85f;
        Draw.centered("KB Client v" + KBClientMod.VERSION, sidebarW / 2f,
                50f + Draw.lineH(titleScale) + 4f,
                Theme.ACCENT, subScale, false);

        Draw.rect(20, 50 + Draw.lineH(titleScale) + Draw.lineH(subScale) + 12, sidebarW - 40, 1, Theme.BORDER);

        KBProfile p = tracker.getProfile();
        if (p.hasData && this.width > sidebarW + 120) {
            String s = "Profile:  " + p.summary();
            int w = Draw.width(s, 0.85f) + 34;
            int px = this.width - w - 14;
            int py = 14;
            Draw.roundRect(px, py, w, 22, 6f, Theme.PANEL2);
            Draw.roundOutline(px, py, w, 22, 6f, 1f, Theme.BORDER);
            Draw.circle(px + 12, py + 11, 3.5f, Theme.GOOD);
            Draw.left(s, px + 22, py + 11, Theme.TEXT, 0.85f, false);
        }

        int userY = this.height - 28;
        Draw.rect(20, userY - 14, sidebarW - 40, 1, Theme.BORDER);

        Draw.roundRect(20, userY - 8, 18, 18, 9f, Theme.PANEL3);
        Draw.centered("L", 29, userY + 1, Theme.SOFT, 1.0f, false);

        Draw.text("Logged in as", 44, userY - 4, Theme.MUTED, 0.75f, false);
        String name = mc.getSession().getUsername();
        String nameF = Draw.fit(name, sidebarW - 56, 0.95f, false);
        Draw.text(nameF, 44, userY + 4, Theme.TEXT, 0.95f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
