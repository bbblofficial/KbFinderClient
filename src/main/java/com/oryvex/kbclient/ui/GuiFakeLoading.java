package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import net.minecraft.client.gui.GuiScreen;
import java.io.IOException;

public class GuiFakeLoading extends GuiScreen {
    private final KBTracker tracker;
    private final long start;

    public GuiFakeLoading(KBTracker tracker) {
        this.tracker = tracker;
        this.start = System.currentTimeMillis();
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        long elapsed = System.currentTimeMillis() - start;
        int pct = (int) Math.min(100, (elapsed * 100) / 3000);
        
        LoadingArt.draw(this.width, this.height, "Loading KB Client", "Initializing modules...", pct);
        
        if (elapsed >= 3000) {
            this.mc.displayGuiScreen(new GuiModernMenu(tracker));
        }
    }
    
    @Override
    protected void keyTyped(char typedChar, int keyCode) throws IOException {
        // Block ESC so they can't skip the fake loading sequence
    }
}
