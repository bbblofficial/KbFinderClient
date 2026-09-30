import os
import re

def fix_kbclient():
    # 1. Generate a safe ProGuard configuration for Forge
    proguard_rules = """-dontshrink
-dontoptimize
-keepattributes *Annotation*,Signature,Exceptions,InnerClasses,EnclosingMethod

# Prevent build failures from unreferenced Minecraft/Forge classes
-dontwarn net.minecraft.**
-dontwarn net.minecraftforge.**
-dontwarn org.apache.**
-dontwarn com.google.**
-dontwarn io.netty.**
-dontwarn org.lwjgl.**
-dontwarn club.minnced.**

# Keep Forge mod entry points and event handlers intact for reflection
-keep @net.minecraftforge.fml.common.Mod class * { *; }
-keepclassmembers class * {
    @net.minecraftforge.fml.common.eventhandler.SubscribeEvent *;
    @net.minecraftforge.fml.common.Mod$EventHandler *;
}

# Protect the mod's core functionality and UI from being mangled
-keep class com.oryvex.kbclient.** { *; }
"""
    with open("proguard-rules.pro", "w", encoding="utf-8") as f:
        f.write(proguard_rules)
    print("Generated safe proguard-rules.pro")

    # 2. Create the Fake Loading Screen
    fake_loading_code = """package com.oryvex.kbclient.ui;

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
"""
    os.makedirs("src/main/java/com/oryvex/kbclient/ui", exist_ok=True)
    with open("src/main/java/com/oryvex/kbclient/ui/GuiFakeLoading.java", "w", encoding="utf-8") as f:
        f.write(fake_loading_code)
    print("Created GuiFakeLoading.java")

    # 3. Patch KBClientMod.java to show the fake loading screen first
    kbclient_path = "src/main/java/com/oryvex/kbclient/KBClientMod.java"
    if os.path.exists(kbclient_path):
        with open(kbclient_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add state tracker so it only loads once per session
        if "private boolean hasFakeLoaded = false;" not in content:
            content = re.sub(
                r'(private boolean loadingInstalled;)', 
                r'\1\n    private boolean hasFakeLoaded = false;', 
                content
            )

        # Inject fake loading redirect
        content = re.sub(
            r'if \(e\.gui instanceof GuiMainMenu\) e\.gui = new GuiModernMenu\(tracker\);',
            r'if (e.gui instanceof GuiMainMenu) {\n            if (!hasFakeLoaded) {\n                e.gui = new com.oryvex.kbclient.ui.GuiFakeLoading(tracker);\n                hasFakeLoaded = true;\n            } else {\n                e.gui = new GuiModernMenu(tracker);\n            }\n        }',
            content
        )

        # Prevent the black fade overlay from applying over the fake loading screen
        content = re.sub(
            r'\} else if \(!\(e\.gui instanceof FadeScreen\) && !\(e\.gui instanceof GuiChat\)\) \{',
            r'} else if (!(e.gui instanceof FadeScreen) && (!(e.gui instanceof GuiChat)) && !(e.gui instanceof com.oryvex.kbclient.ui.GuiFakeLoading)) {',
            content
        )

        with open(kbclient_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully patched KBClientMod.java")
    else:
        print(f"Error: Could not find {kbclient_path}")

if __name__ == "__main__":
    fix_kbclient()