package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiOptions;
import net.minecraft.client.gui.GuiScreen;

public class GuiKbOptions extends FadeScreen {
    private final KBTracker tracker;
    private final GuiScreen parent;
    private UiButton bHud, bPart, bToast, bLoad, bFade, bDisc;
    private int cardX, cardY, cardW, cardH;

    public GuiKbOptions(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        int bw = Math.min(280, this.width - 80);
        int bh = 24;
        int gap = 6;
        int cx = this.width / 2;

        int rows = 6;
        int innerH = rows * (bh + gap) + gap + 2 * (bh + gap) + 12;
        cardW = bw + 48;
        cardH = innerH + 90;
        cardX = cx - cardW / 2;
        cardY = Math.max(24, (this.height - cardH) / 2);

        int y = cardY + 74;
        int bx = cx - bw / 2;

        bHud   = new UiButton(1, bx, y,                       bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(40);
        bPart  = new UiButton(2, bx, y + 1 * (bh + gap),      bw, bh, "Menu particles").style(UiButton.TOGGLE).delay(70);
        bToast = new UiButton(3, bx, y + 2 * (bh + gap),      bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(100);
        bLoad  = new UiButton(4, bx, y + 3 * (bh + gap),      bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(130);
        bDisc  = new UiButton(8, bx, y + 4 * (bh + gap),      bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(160);
        bFade  = new UiButton(5, bx, y + 5 * (bh + gap),      bw, bh, "").delay(190);

        this.buttonList.add(bHud);
        this.buttonList.add(bPart);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bDisc);
        this.buttonList.add(bFade);

        int y2 = y + 6 * (bh + gap) + 12;
        this.buttonList.add(new UiButton(6, bx, y2,             bw, bh, "Minecraft Options...").icon(Draw.ICON_GEAR).delay(220));
        this.buttonList.add(new UiButton(7, bx, y2 + bh + gap,  bw, bh, "Done").style(UiButton.PRIMARY).icon(Draw.ICON_CHECK).delay(250));

        sync();
    }

    private void sync() {
        bHud.on = Settings.hud;
        bPart.on = false; // particles removed
        bToast.on = Settings.toasts;
        bLoad.on = Settings.customLoading;
        bDisc.on = Settings.discordRpc;
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: Settings.hud = !Settings.hud; break;
            case 2: /* particles removed — toggle no-op */ break;
            case 3: Settings.toasts = !Settings.toasts; break;
            case 4: Settings.customLoading = !Settings.customLoading; break;
            case 8: Settings.discordRpc = !Settings.discordRpc; com.oryvex.kbclient.DiscordRPC.apply(); break;
            case 5: Settings.fade = (Settings.fade + 1) % 4; break;
            case 6: closeTo(new GuiOptions(this, this.mc.gameSettings)); return;
            case 7: Settings.save(); closeTo(parent); return;
            default: break;
        }
        Settings.save();
        sync();
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        if (key == org.lwjgl.input.Keyboard.KEY_ESCAPE) { Settings.save(); closeTo(parent); }
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);

        Draw.panel(cardX, cardY, cardW, cardH, 10f, Theme.SURFACE, Theme.BORDER);

        float cx = this.width / 2f;
        Draw.centered("OPTIONS", cx, cardY + 26, Theme.TEXT, 1.8f, false);
        Draw.centered("KB Client preferences", cx, cardY + 50, Theme.MUTED, 0.9f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
