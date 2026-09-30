import os
import re

def patch_terrain_loading():
    # 1. Create GuiFakeWorldLoad.java
    fake_world_load_code = """package com.oryvex.kbclient.ui;

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
"""
    os.makedirs("src/main/java/com/oryvex/kbclient/ui", exist_ok=True)
    with open("src/main/java/com/oryvex/kbclient/ui/GuiFakeWorldLoad.java", "w", encoding="utf-8") as f:
        f.write(fake_world_load_code)
    print("Created GuiFakeWorldLoad.java")

    # 2. Patch KBClientMod.java to intercept the world entry
    kbclient_path = "src/main/java/com/oryvex/kbclient/KBClientMod.java"
    if os.path.exists(kbclient_path):
        with open(kbclient_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "GuiFakeWorldLoad" not in content:
            # Hook the moment the world loads in onTick to show the fake screen
            content = re.sub(
                r'if\s*\(\s*mc\.theWorld\s*!=\s*lastWorld\s*\)\s*\{\s*lastWorld\s*=\s*mc\.theWorld;\s*if\s*\(\s*mc\.theWorld\s*!=\s*null\s*&&\s*Fade\.ms\(\)\s*>\s*0\s*\)\s*Fade\.world\.trigger\(1f,\s*Fade\.ms\(\)\s*\*\s*3L\);\s*\}',
                r'if (mc.theWorld != lastWorld) {\n            lastWorld = mc.theWorld;\n            if (mc.theWorld != null) {\n                if (Fade.ms() > 0) Fade.world.trigger(1f, Fade.ms() * 3L);\n                mc.displayGuiScreen(new com.oryvex.kbclient.ui.GuiFakeWorldLoad());\n            }\n        }',
                content
            )
            
            # Prevent the Fade overlay from stacking darkly over this specific GUI
            content = content.replace(
                "!(e.gui instanceof com.oryvex.kbclient.ui.GuiFakeLoading)) {",
                "!(e.gui instanceof com.oryvex.kbclient.ui.GuiFakeLoading) && !(e.gui instanceof com.oryvex.kbclient.ui.GuiFakeWorldLoad)) {"
            )
            content = content.replace(
                "!(e.gui instanceof GuiChat)) {",
                "!(e.gui instanceof GuiChat) && !(e.gui instanceof com.oryvex.kbclient.ui.GuiFakeWorldLoad)) {"
            )

            with open(kbclient_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully patched KBClientMod.java")
        else:
            print("KBClientMod.java is already patched.")
    else:
        print(f"Error: Could not find {kbclient_path}")

if __name__ == "__main__":
    patch_terrain_loading()