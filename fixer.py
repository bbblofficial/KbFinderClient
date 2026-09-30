import os
import re

def restore_gui_analyzer():
    path = "src/main/java/com/oryvex/kbclient/ui/GuiAnalyzer.java"
    if not os.path.exists(path):
        print(f"Error: Could not find {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Restore the original labels array
    content = content.replace(
        'String[] labels = { "Import", "Copy YAML", "Export", "Reset", "Pause", "Reconnect", "Close" };',
        'String[] labels = { "Import", "Copy YAML", "Export", "Reset", "Pause", "Close" };'
    )
    
    # Restore width and total span calculation
    content = content.replace(
        'int bw = Math.min(62, (pw - 20) / 7);',
        'int bw = Math.min(76, (pw - 20) / 6);'
    )
    content = content.replace(
        'int total = 7 * bw + 6 * 4;',
        'int total = 6 * bw + 5 * 4;'
    )
    
    # Restore loop size
    content = content.replace(
        'for (int i = 0; i < 7; i++) {',
        'for (int i = 0; i < 6; i++) {'
    )

    # Restore switch cases
    modified_cases = """            case 104:
                tracker.setRecording(!tracker.isRecording());
                break;
            case 105:
                if (this.mc != null && this.mc.thePlayer != null) this.mc.thePlayer.sendChatMessage("/findkb []");
                toast("Sent /findkb []", true);
                break;
            case 106:
                closeTo(parent);
                break;"""
                
    original_cases = """            case 104:
                tracker.setRecording(!tracker.isRecording());
                break;
            case 105:
                closeTo(parent);
                break;"""
                
    content = content.replace(modified_cases, original_cases)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Restored: GuiAnalyzer.java (Removed Reconnect button)")


def restore_settings():
    path = "src/main/java/com/oryvex/kbclient/ui/Settings.java"
    if not os.path.exists(path):
        print(f"Error: Could not find {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Restore default boolean fields
    content = re.sub(r'public static boolean hud = false;', 'public static boolean hud = true;', content)
    content = re.sub(r'public static boolean particles = false;', 'public static boolean particles = true;', content)
    content = re.sub(r'public static boolean toasts = false;', 'public static boolean toasts = true;', content)
    content = re.sub(r'public static boolean customLoading = false;', 'public static boolean customLoading = true;', content)
    content = re.sub(r'public static boolean discordRpc = false;', 'public static boolean discordRpc = true;', content)

    # Restore parseBoolean load methods
    content = re.sub(r'hud = false;', 'hud = Boolean.parseBoolean(p.getProperty("hud", "true"));', content)
    content = re.sub(r'particles = false;', 'particles = Boolean.parseBoolean(p.getProperty("particles", "true"));', content)
    content = re.sub(r'toasts = false;', 'toasts = Boolean.parseBoolean(p.getProperty("toasts", "true"));', content)
    content = re.sub(r'customLoading = false;', 'customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));', content)
    content = re.sub(r'discordRpc = false;', 'discordRpc = Boolean.parseBoolean(p.getProperty("discordRpc", "true"));', content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Restored: Settings.java (Re-enabled default features)")


def restore_gui_options():
    path = "src/main/java/com/oryvex/kbclient/ui/GuiKbOptions.java"
    if not os.path.exists(path):
        print(f"Error: Could not find {path}")
        return

    # Fully restore the options screen with all original toggles
    original_content = """package com.oryvex.kbclient.ui;

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
        int bw = 216, bh = 20, gap = 6, cx = this.width / 2;
        int y = Math.max(54, this.height / 2 - 93);
        cardW = bw + 28;
        cardX = cx - cardW / 2;
        cardY = y - 42;
        cardH = 8 * (bh + gap) + 62;

        bHud = new UiButton(1, cx - bw / 2, y, bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(60);
        bPart = new UiButton(2, cx - bw / 2, y + (bh + gap), bw, bh, "Menu particles").style(UiButton.TOGGLE).delay(110);
        bToast = new UiButton(3, cx - bw / 2, y + 2 * (bh + gap), bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(160);
        bLoad = new UiButton(4, cx - bw / 2, y + 3 * (bh + gap), bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(210);
        bFade = new UiButton(5, cx - bw / 2, y + 4 * (bh + gap), bw, bh, "").delay(260);
        bDisc = new UiButton(8, cx - bw / 2, y + 5 * (bh + gap), bw, bh, "Discord Rich Presence").style(UiButton.TOGGLE).delay(285);
        
        this.buttonList.add(bHud);
        this.buttonList.add(bPart);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bFade);
        this.buttonList.add(bDisc);
        this.buttonList.add(new UiButton(6, cx - bw / 2, y + 6 * (bh + gap) + 8, bw, bh, "Minecraft Options...").icon(UiButton.ICON_GEAR).delay(310));
        this.buttonList.add(new UiButton(7, cx - bw / 2, y + 7 * (bh + gap) + 8, bw, bh, "Done").style(UiButton.PRIMARY).delay(360));
        sync();
    }

    private void sync() {
        bHud.on = Settings.hud;
        bPart.on = Settings.particles;
        bToast.on = Settings.toasts;
        bLoad.on = Settings.customLoading;
        bDisc.on = Settings.discordRpc;
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: Settings.hud = !Settings.hud; break;
            case 2: Settings.particles = !Settings.particles; break;
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
        drawBackdrop(30);
        Draw.panel(cardX, cardY, cardW, cardH, 8, Theme.GLASS, Theme.BORDER);
        Draw.centered("OPTIONS", this.width / 2f, cardY + 10, Theme.TEXT, 1.6f, true);
        Draw.centered("KB Client preferences", this.width / 2f, cardY + 26, Theme.MUTED, 0.8f, false);
        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    print("Restored: GuiKbOptions.java (Restored all option toggles)")

if __name__ == "__main__":
    print("Reverting KB Client back to default...")
    restore_gui_analyzer()
    restore_settings()
    restore_gui_options()
    print("Done!")