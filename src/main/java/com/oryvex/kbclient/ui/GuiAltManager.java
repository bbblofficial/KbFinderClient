
package com.oryvex.kbclient.ui;

import java.io.IOException;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.GuiTextField;
import net.minecraft.util.Session;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import org.lwjgl.input.Keyboard;

public class GuiAltManager extends FadeScreen {
    private final GuiScreen parent;
    private GuiTextField nameField;
    private String status = "Ready";
    private int statusColor = Theme.DIM;
    private int cardX, cardY, cardW, cardH;
    private int cx, y, bw;

    public GuiAltManager(GuiScreen parent) {
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        Keyboard.enableRepeatEvents(true);
        bw = 200;
        int bh = 22, gap = 6;
        cx = this.width / 2;
        y = this.height / 2 - 45;
        cardW = bw + 40;
        cardX = cx - cardW / 2;
        cardY = y - 35;
        cardH = 175;

        // فیلد متنی کاستوم بدون پس‌زمینه دیفالت ماینکرفت
        nameField = new GuiTextField(0, this.fontRendererObj, cx - bw / 2 + 5, y + 14, bw - 10, 12);
        nameField.setMaxStringLength(16);
        nameField.setFocused(true);
        nameField.setEnableBackgroundDrawing(false);
        nameField.setTextColor(Theme.TEXT);

        this.buttonList.add(new UiButton(1, cx - bw / 2, y + 45, bw, bh, "Login (Offline)").style(UiButton.PRIMARY).delay(60));
        this.buttonList.add(new UiButton(2, cx - bw / 2, y + 45 + bh + gap, bw, bh, "Generate Random Alt").delay(110));
        this.buttonList.add(new UiButton(3, cx - bw / 2, y + 45 + 2 * (bh + gap), bw, bh, "Back").style(UiButton.DANGER).delay(160));
    }

    @Override
    public void onGuiClosed() {
        Keyboard.enableRepeatEvents(false);
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1:
                login(nameField.getText());
                break;
            case 2:
                String randomName = "KBAlt_" + (1000 + new java.util.Random().nextInt(9000));
                nameField.setText(randomName);
                login(randomName);
                break;
            case 3:
                closeTo(parent);
                break;
        }
    }

    private void login(String name) {
        if (name == null || name.trim().isEmpty()) {
            status = "Username cannot be empty!";
            statusColor = Theme.BAD;
            return;
        }
        try {
            // تغییر توکن سشن ماینکرفت از طریق Reflection برای بای‌پس حالت آفلاین
            Session newSession = new Session(name.trim(), "", "", "mojang");
            ObfuscationReflectionHelper.setPrivateValue(Minecraft.class, this.mc, newSession, "session", "field_71449_j");
            status = "Logged in as " + name;
            statusColor = Theme.GOOD;
        } catch (Exception e) {
            status = "Failed to set session!";
            statusColor = Theme.BAD;
        }
    }

    @Override
    protected void onKey(char typedChar, int keyCode) throws IOException {
        if (nameField.isFocused()) {
            nameField.textboxKeyTyped(typedChar, keyCode);
            if (keyCode == Keyboard.KEY_RETURN) login(nameField.getText());
        }
        if (keyCode == Keyboard.KEY_ESCAPE) closeTo(parent);
    }

    @Override
    protected void mouseClicked(int mouseX, int mouseY, int mouseButton) throws IOException {
        super.mouseClicked(mouseX, mouseY, mouseButton);
        nameField.mouseClicked(mouseX, mouseY, mouseButton);
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        drawBackdrop(20);
        Draw.panel(cardX, cardY, cardW, cardH, 8, Theme.GLASS, Theme.BORDER);
        Draw.centered("ALT MANAGER", cx, cardY + 12, Theme.TEXT, 1.4f, true);
        Draw.centered("Current: " + this.mc.getSession().getUsername(), cx, cardY + 30, Theme.ACCENT, 0.85f, false);
        
        // استایل مدرن دور Text Box
        Draw.roundRect(cx - bw / 2f, y + 10, bw, 20, 4f, Theme.PANEL3);
        if (nameField.isFocused()) Draw.shadow(cx - bw / 2f, y + 10, bw, 20, 4f, Draw.fade(Theme.ACCENT, 0.4f), 3f);
        nameField.drawTextBox();

        // رسم وضعیت ارور یا موفقیت
        Draw.centered(status, cx, cardY + cardH - 16, statusColor, 0.85f, false);
        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
