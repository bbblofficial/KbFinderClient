package com.oryvex.kbclient.ui;

import net.minecraft.client.gui.GuiScreen;
import java.io.IOException;

public class GuiFakeWorldLoad extends GuiScreen {
    private final long start;

    public GuiFakeWorldLoad() {
        this.start = System.currentTimeMillis();
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        long elapsed = System.currentTimeMillis() - start;
        int pct = (int) Math.min(100, (elapsed * 100) / 3000);
        
        LoadingArt.draw(this.width, this.height, "Joining world", "Initializing client modules...", pct);
        
        if (elapsed >= 3000) {
            this.mc.displayGuiScreen(null);
        }
    }
    
    @Override
    protected void keyTyped(char typedChar, int keyCode) throws IOException {
        // Block ESC so they can't skip the fake loading sequence
    }
    
    @Override
    public boolean doesGuiPauseGame() {
        // Must be false so the server doesn't time out and chunks load in the background
        return false;
    }
}
