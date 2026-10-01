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
        sidebarW = Math.max(200, Math.min(320, (int)(this.width * 0.30f)));

        int padding = 22;
        int bw = sidebarW - padding * 2;
        int bh = 26;
        int gap = 8;
        int totalH = 6 * bh + 5 * gap;
        int top = Math.max(110, (this.height - totalH) / 2 + 16);

        this.buttonList.add(new UiButton(1, padding, top,                   bw, bh, "Singleplayer").icon(Draw.ICON_PLAY).delay(40));
        this.buttonList.add(new UiButton(2, padding, top + 1 * (bh + gap),  bw, bh, "Multiplayer").icon(Draw.ICON_GRAPH).delay(70));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap),  bw, bh, "Alt Manager").icon(Draw.ICON_USER).delay(100));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap),  bw, bh, "Analyzer").style(UiButton.PRIMARY).icon(Draw.ICON_GEAR).delay(130));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap),  bw, bh, "Options").icon(Draw.ICON_GEAR).delay(160));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap),  bw, bh, "Quit").style(UiButton.DANGER).icon(Draw.ICON_CLOSE).delay(190));
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: closeTo(new GuiSelectWorld(this)); break;
            case 2: closeTo(new GuiMultiplayer(this)); break;
            case 3: closeTo(new GuiAnalyzer(tracker, this)); break;
            case 4: closeTo(new GuiKbOptions(tracker, this)); break;
            case 6: closeTo(new GuiAltManager(this)); break;
            case 5: closeThen(new Runnable() { @Override public void run() { mc.shutdown(); } }); break;
            default: break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException { }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);
        Draw.rect(0, 0, sidebarW, this.height, Theme.SURFACE);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // ---- Title ----
        float titleScale = Math.max(1.5f, Math.min(2.2f, sidebarW / 140f));
        Draw.centered("ORYVEX", sidebarW / 2f, 52f, Theme.TEXT, titleScale, false);

        float subScale = 0.85f;
        Draw.centered("KB Client v" + KBClientMod.VERSION, sidebarW / 2f,
                52f + Draw.lineH(titleScale) + 6f, Theme.MUTED, subScale, false);

        float divY = 52f + Draw.lineH(titleScale) + Draw.lineH(subScale) + 16f;
        Draw.rect(sidebarW * 0.2f, divY, sidebarW * 0.6f, 1f, Theme.BORDER);

        // ---- Profile chip (top-right) ----
        KBProfile p = tracker.getProfile();
        if (p.hasData && this.width > sidebarW + 160) {
            String s = p.summary();
            int w = Draw.width(s, 0.85f) + 46;
            int px = this.width - w - 18;
            int py = 18;
            Draw.roundRect(px, py, w, 26, 6f, Theme.SURFACE2);
            Draw.roundOutline(px, py, w, 26, 6f, 1f, Theme.BORDER);
            Draw.circle(px + 14, py + 13, 4f, Theme.GOOD);
            Draw.left("Profile", px + 26, py + 8, Theme.MUTED, 0.72f, false);
            Draw.left(s,       px + 26, py + 18, Theme.TEXT, 0.85f, false);
        }

        // ---- User card (bottom-left) ----
        int userY = this.height - 34;
        Draw.rect(sidebarW * 0.2f, userY - 18, sidebarW * 0.6f, 1f, Theme.BORDER);

        int avX = 22, avY = userY - 8;
        Draw.roundRect(avX, avY, 22, 22, 11f, Theme.SURFACE3);
        Draw.icon(Draw.ICON_USER, avX + 11f, avY + 11f, 12f, Theme.SOFT);

        Draw.left("Logged in as", 52, userY - 2, Theme.MUTED, 0.72f, false);
        String name = mc.getSession().getUsername();
        String nameF = Draw.fit(name, sidebarW - 70, 0.9f, false);
        Draw.left(nameF, 52, userY + 8, Theme.TEXT, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
