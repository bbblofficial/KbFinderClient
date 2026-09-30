import os
import re

def fix_gui_analyzer():
    path = "src/main/java/com/oryvex/kbclient/ui/GuiAnalyzer.java"
    if not os.path.exists(path):
        print(f"Error: Could not find {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add the Reconnect button to the labels array
    content = content.replace(
        'String[] labels = { "Import", "Copy YAML", "Export", "Reset", "Pause", "Close" };',
        'String[] labels = { "Import", "Copy YAML", "Export", "Reset", "Pause", "Reconnect", "Close" };'
    )
    
    # Adjust width and total span calculation for 7 buttons instead of 6
    content = content.replace(
        'int bw = Math.min(76, (pw - 20) / 6);',
        'int bw = Math.min(62, (pw - 20) / 7);'
    )
    content = content.replace(
        'int total = 6 * bw + 5 * 4;',
        'int total = 7 * bw + 6 * 4;'
    )
    
    # Adjust loop size
    content = content.replace(
        'for (int i = 0; i < 6; i++) {',
        'for (int i = 0; i < 7; i++) {'
    )

    # Insert action case 105 for Reconnect and shift Close to 106
    old_cases = """            case 104:
                tracker.setRecording(!tracker.isRecording());
                break;
            case 105:
                closeTo(parent);
                break;"""
                
    new_cases = """            case 104:
                tracker.setRecording(!tracker.isRecording());
                break;
            case 105:
                if (this.mc != null && this.mc.thePlayer != null) this.mc.thePlayer.sendChatMessage("/findkb []");
                toast("Sent /findkb []", true);
                break;
            case 106:
                closeTo(parent);
                break;"""
                
    content = content.replace(old_cases, new_cases)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated: GuiAnalyzer.java (Added Reconnect button)")

def fix_settings():
    path = "src/main/java/com/oryvex/kbclient/ui/Settings.java"
    if not os.path.exists(path):
        print(f"Error: Could not find {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Disable all non-fade settings by default
    content = re.sub(r'public static boolean hud = true;', 'public static boolean hud = false;', content)
    content = re.sub(r'public static boolean particles = true;', 'public static boolean particles = false;', content)
    content = re.sub(r'public static boolean toasts = true;', 'public static boolean toasts = false;', content)
    content = re.sub(r'public static boolean customLoading = true;', 'public static boolean customLoading = false;', content)
    content = re.sub(r'public static boolean discordRpc = true;', 'public static boolean discordRpc = false;', content)

    # Force them to remain false even if an old config tries to load them
    content = re.sub(r'hud = Boolean\.parseBoolean\(.*?\);', 'hud = false;', content)
    content = re.sub(r'particles = Boolean\.parseBoolean\(.*?\);', 'particles = false;', content)
    content = re.sub(r'toasts = Boolean\.parseBoolean\(.*?\);', 'toasts = false;', content)
    content = re.sub(r'customLoading = Boolean\.parseBoolean\(.*?\);', 'customLoading = false;', content)
    content = re.sub(r'discordRpc = Boolean\.parseBoolean\(.*?\);', 'discordRpc = false;', content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated: Settings.java (Disabled all non-fade animations/UI)")

def fix_gui_options():
    path = "src/main/java/com/oryvex/kbclient/ui/GuiKbOptions.java"
    if not os.path.exists(path):
        print(f"Error: Could not find {path}")
        return

    # Fully replace the options screen to strictly feature only the Fade preference
    new_content = """package com.oryvex.kbclient.ui;

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
"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Updated: GuiKbOptions.java (Removed toggles for stripped features)")

if __name__ == "__main__":
    print("Applying changes for KB Client...")
    fix_gui_analyzer()
    fix_settings()
    fix_gui_options()
    print("Done!")