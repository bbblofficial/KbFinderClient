import os

def apply_fixes():
    # 1. Update GuiFakeLoading to use FadeScreen for smooth transitions
    fake_main_loading = """package com.oryvex.kbclient.ui;

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
"""
    
    # 2. Update GuiFakeWorldLoad to use FadeScreen for smooth transitions
    fake_world_loading = """package com.oryvex.kbclient.ui;

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
"""
    
    os.makedirs("src/main/java/com/oryvex/kbclient/ui", exist_ok=True)
    with open("src/main/java/com/oryvex/kbclient/ui/GuiFakeLoading.java", "w", encoding="utf-8") as f:
        f.write(fake_main_loading)
    with open("src/main/java/com/oryvex/kbclient/ui/GuiFakeWorldLoad.java", "w", encoding="utf-8") as f:
        f.write(fake_world_loading)

    print("✅ Upgraded Fake Loading Screens with FadeScreen animations.")

    # 3. Patch KBClientMod.java to redirect the pause menu options to GuiKbOptions
    kbclient_path = "src/main/java/com/oryvex/kbclient/KBClientMod.java"
    if os.path.exists(kbclient_path):
        with open(kbclient_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "public void onActionPerformed" not in content:
            interceptor = """
    @SubscribeEvent
    public void onActionPerformed(net.minecraftforge.client.event.GuiScreenEvent.ActionPerformedEvent.Pre e) {
        // When clicking the 'Options' button (ID 0) in the pause menu, open KB Client Options instead
        if (e.gui instanceof net.minecraft.client.gui.GuiIngameMenu && e.button.id == 0) {
            e.setCanceled(true);
            net.minecraft.client.Minecraft.getMinecraft().displayGuiScreen(new com.oryvex.kbclient.ui.GuiKbOptions(tracker, e.gui));
        }
    }

    @SubscribeEvent
    public void onOverlay"""
            
            # Injecting right before onOverlay to ensure we don't break regex bounds
            content = content.replace("@SubscribeEvent\n    public void onOverlay", interceptor)

            with open(kbclient_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ Patched KBClientMod.java to open Discord RPC / KB Options from the Pause Menu.")
        else:
            print("ℹ️ KBClientMod.java already contains the pause menu interceptor.")

if __name__ == "__main__":
    apply_fixes()