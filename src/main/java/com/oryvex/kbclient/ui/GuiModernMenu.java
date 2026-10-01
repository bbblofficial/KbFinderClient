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

        // responsive sidebar: ~30% width, min 200, max 320
        sidebarW = Math.max(200, Math.min(320, (int)(this.width * 0.30f)));

        int padding = 24;
        int bw = sidebarW - padding * 2;
        int bh = 26;
        int gap = 8;

        int totalH = 6 * bh + 5 * gap;
        int top = Math.max(110, (this.height - totalH) / 2 + 20);

        this.buttonList.add(new UiButton(1, padding, top,                       bw, bh, "Singleplayer").icon(Draw.ICON_PLAY).delay(60));
        this.buttonList.add(new UiButton(2, padding, top + 1 * (bh + gap),      bw, bh, "Multiplayer").icon(Draw.ICON_GRAPH).delay(100));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap),      bw, bh, "Alt Manager").icon(Draw.ICON_USER).delay(140));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap),      bw, bh, "Analyzer").style(UiButton.PRIMARY).icon(Draw.ICON_GEAR).delay(180));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap),      bw, bh, "Options").icon(Draw.ICON_GEAR).delay(220));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap),      bw, bh, "Quit").style(UiButton.DANGER).icon(Draw.ICON_CLOSE).delay(260));
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
        // main menu cannot be closed with ESC
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);

        // ambient particles
        if (Settings.particles && Settings.density > 0) {
            Draw.plexusBackground(this.width, this.height, 0.35f);
        }

        // sidebar panel
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // ---- Title ----
        float titleScale = Math.max(1.6f, Math.min(2.4f, sidebarW / 130f));
        Draw.centered("ORYVEX", sidebarW / 2f, 55f, Theme.TEXT, titleScale, true);

        float subScale = 0.9f;
        float subY = 55f + Draw.lineH(titleScale) + 8f;
        Draw.centered("KB Client v" + KBClientMod.VERSION, sidebarW / 2f, subY, Theme.ACCENT, subScale, false);

        // divider
        int divY = (int)(subY + Draw.lineH(subScale) + 12f);
        Draw.rect(40, divY, sidebarW - 80, 1, Theme.BORDER);

        // ---- Profile chip (top-right) ----
        KBProfile p = tracker.getProfile();
        if (p.hasData && this.width > sidebarW + 160) {
            String s = p.summary();
            int w = Draw.width(s, 0.85f) + 48;
            int px = this.width - w - 18;
            int py = 18;
            Draw.roundRect(px, py, w, 26, 6f, Theme.PANEL2);
            Draw.roundOutline(px, py, w, 26, 6f, 1f, Theme.BORDER);
            Draw.circle(px + 14, py + 13, 4f, Theme.GOOD);
            Draw.left("Profile", px + 26, py + 8, Theme.MUTED, 0.7f, false);
            Draw.left(s,       px + 26, py + 18, Theme.TEXT, 0.85f, false);
        }

        // ---- User card (bottom-left) ----
        int userY = this.height - 36;
        Draw.rect(40, userY - 18, sidebarW - 80, 1, Theme.BORDER);

        // avatar circle
        int avX = 34, avY = userY - 8;
        Draw.roundRect(avX, avY, 22, 22, 11f, Theme.PANEL3);
        Draw.icon(Draw.ICON_USER, avX + 11f, avY + 11f, 12f, Theme.SOFT);

        Draw.left("Logged in as", 64, userY - 2, Theme.MUTED, 0.72f, false);
        String name = mc.getSession().getUsername();
        String nameF = Draw.fit(name, sidebarW - 80, 0.9f, false);
        Draw.left(nameF, 64, userY + 8, Theme.TEXT, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
