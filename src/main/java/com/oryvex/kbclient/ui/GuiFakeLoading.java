package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import java.io.IOException;

public class GuiFakeLoading extends FadeScreen {
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
        
        // Start the fade-out animation 300ms before finishing
        if (elapsed >= 2700 && !this.isClosing()) {
            this.closeTo(new GuiModernMenu(tracker));
        }
        
        LoadingArt.draw(this.width, this.height, "Loading KB Client", "Initializing modules...", pct);
        
        super.drawScreen(mouseX, mouseY, partialTicks);
        this.drawFade();
    }
    
    @Override
    protected void onKey(char c, int key) throws IOException {
        // Block ESC
    }
}
