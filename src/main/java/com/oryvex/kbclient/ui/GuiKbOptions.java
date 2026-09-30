package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiOptions;
import net.minecraft.client.gui.GuiScreen;

public class GuiKbOptions extends FadeScreen {
    private final KBTracker tracker;
    private final GuiScreen parent;
    private UiButton bFade;
    private int cardX, cardY, cardW, cardH;

    public GuiKbOptions(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        int bw = 216, bh = 20, gap = 6, cx = this.width / 2;
        int y = Math.max(54, this.height / 2 - 40);
        cardW = bw + 28;
        cardX = cx - cardW / 2;
        cardY = y - 42;
        cardH = 3 * (bh + gap) + 62;

        bFade = new UiButton(5, cx - bw / 2, y, bw, bh, "").delay(60);
        this.buttonList.add(bFade);
        this.buttonList.add(new UiButton(6, cx - bw / 2, y + 1 * (bh + gap) + 8, bw, bh, "Minecraft Options...").icon(UiButton.ICON_GEAR).delay(110));
        this.buttonList.add(new UiButton(7, cx - bw / 2, y + 2 * (bh + gap) + 8, bw, bh, "Done").style(UiButton.PRIMARY).delay(160));
        sync();
    }

    private void sync() {
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
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
        drawBackdrop(0); // Forces 0 menu particles
        Draw.panel(cardX, cardY, cardW, cardH, 8, Theme.GLASS, Theme.BORDER);
        Draw.centered("OPTIONS", this.width / 2f, cardY + 10, Theme.TEXT, 1.6f, true);
        Draw.centered("KB Client preferences", this.width / 2f, cardY + 26, Theme.MUTED, 0.8f, false);
        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
