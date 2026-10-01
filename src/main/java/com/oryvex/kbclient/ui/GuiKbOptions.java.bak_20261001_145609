package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiOptions;
import net.minecraft.client.gui.GuiScreen;

/**
 * Centered, flat options screen for KB Client.
 *
 *   ┌──────────────────────────────────────┐
 *   │              OPTIONS                 │
 *   │       KB Client preferences          │
 *   │            ─────────                 │
 *   │  HUD overlay              [toggle]   │
 *   │  Hit toasts               [toggle]   │
 *   │  Custom loading screen    [toggle]   │
 *   │  Discord Rich Presence    [toggle]   │
 *   │  Screen fades: Normal                │
 *   │      [ ⚙ MC Options ]  [ ✓ Done ]    │
 *   │      KB Client 3.0 | Forge 1.8.9     │
 *   └──────────────────────────────────────┘
 *
 * The legacy "Menu particles" toggle has been removed.
 */
public class GuiKbOptions extends FadeScreen {

    private final KBTracker tracker;
    private final GuiScreen parent;

    private UiButton bHud, bToast, bLoad, bDisc, bFade;

    private int cardX, cardY, cardW, cardH;

    public GuiKbOptions(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent  = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();

        int cx = this.width / 2;

        int bw  = Math.min(300, this.width - 80);
        int bh  = 22;
        int gap = 5;

        int pad        = 24;
        int headerH    = 88;
        int togglesH   = 5 * (bh + gap) - gap;   // 130
        int actionsGap = 12;
        int actionsH   = bh;                     // 22
        int footerH    = 40;

        cardW = bw + pad * 2;
        cardH = pad + headerH + togglesH + actionsGap + actionsH + footerH + pad;
        cardX = cx - cardW / 2;
        cardY = Math.max(16, (this.height - cardH) / 2);

        int togglesY = cardY + pad + headerH;
        int bx       = cx - bw / 2;

        bHud   = new UiButton(1, bx, togglesY,                    bw, bh, "HUD overlay")
                        .style(UiButton.TOGGLE).delay(50);
        bToast = new UiButton(3, bx, togglesY + 1 * (bh + gap),   bw, bh, "Hit toasts")
                        .style(UiButton.TOGGLE).delay(90);
        bLoad  = new UiButton(4, bx, togglesY + 2 * (bh + gap),   bw, bh, "Custom loading screen")
                        .style(UiButton.TOGGLE).delay(130);
        bDisc  = new UiButton(8, bx, togglesY + 3 * (bh + gap),   bw, bh, "Discord Rich Presence")
                        .style(UiButton.TOGGLE).delay(170);
        bFade  = new UiButton(5, bx, togglesY + 4 * (bh + gap),   bw, bh, "")
                        .delay(210);

        this.buttonList.add(bHud);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bDisc);
        this.buttonList.add(bFade);

        int actionY   = togglesY + togglesH + actionsGap;
        int actionGap = 8;
        int halfW     = (bw - actionGap) / 2;

        UiButton mcOpt = new UiButton(6, bx, actionY, halfW, bh, "MC Options");
        mcOpt.icon(Draw.ICON_GEAR).delay(250);

        UiButton done = new UiButton(7, bx + halfW + actionGap, actionY, halfW, bh, "Done");
        done.style(UiButton.PRIMARY).icon(Draw.ICON_CHECK).delay(290);

        this.buttonList.add(mcOpt);
        this.buttonList.add(done);

        sync();
    }

    private void sync() {
        bHud.on   = Settings.hud;
        bToast.on = Settings.toasts;
        bLoad.on  = Settings.customLoading;
        bDisc.on  = Settings.discordRpc;
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: Settings.hud           = !Settings.hud;           break;
            case 3: Settings.toasts        = !Settings.toasts;        break;
            case 4: Settings.customLoading = !Settings.customLoading; break;
            case 8:
                Settings.discordRpc = !Settings.discordRpc;
                com.oryvex.kbclient.DiscordRPC.apply();
                break;
            case 5: Settings.fade = (Settings.fade + 1) % 4;          break;
            case 6: closeTo(new GuiOptions(this, this.mc.gameSettings)); return;
            case 7: Settings.save(); closeTo(parent);                    return;
            default: break;
        }
        Settings.save();
        sync();
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        if (key == org.lwjgl.input.Keyboard.KEY_ESCAPE) {
            Settings.save();
            closeTo(parent);
        }
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        // Flat full-screen backdrop
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);

        // Centered card
        Draw.panel(cardX, cardY, cardW, cardH, 10f, Theme.SURFACE, Theme.BORDER);

        float cx = this.width / 2f;

        // ---- Header -------------------------------------------------
        float titleCY = cardY + 44f;
        Draw.centered("OPTIONS",               cx, titleCY,        Theme.TEXT,  1.8f,  false);
        Draw.centered("KB Client preferences", cx, titleCY + 24f,  Theme.MUTED, 0.85f, false);
        Draw.rect(cx - 30f, titleCY + 42f, 60f, 1f, Theme.BORDER);

        // ---- Footer -------------------------------------------------
        Draw.centered("KB Client 3.0  |  Forge 1.8.9",
                cx, cardY + cardH - 20f, Theme.DIM, 0.7f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
