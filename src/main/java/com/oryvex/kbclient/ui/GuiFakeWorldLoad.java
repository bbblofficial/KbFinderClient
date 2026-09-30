package com.oryvex.kbclient.ui;

import java.io.IOException;

public class GuiFakeWorldLoad extends FadeScreen {
    private final long start;

    public GuiFakeWorldLoad() {
        this.start = System.currentTimeMillis();
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        long elapsed = System.currentTimeMillis() - start;
        int pct = (int) Math.min(100, (elapsed * 100) / 3000);
        
        // Start the fade-out animation 300ms before finishing
        if (elapsed >= 2700 && !this.isClosing()) {
            this.closeTo(null);
        }
        
        LoadingArt.draw(this.width, this.height, "Joining world", "Initializing client modules...", pct);
        
        super.drawScreen(mouseX, mouseY, partialTicks);
        this.drawFade();
    }
    
    @Override
    protected void onKey(char c, int key) throws IOException {
        // Block ESC
    }
    
    @Override
    public boolean doesGuiPauseGame() {
        return false;
    }
}
