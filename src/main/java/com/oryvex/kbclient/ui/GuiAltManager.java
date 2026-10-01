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
    private int statusColor = Theme.MUTED;
    private int cardX, cardY, cardW, cardH;
    private int cx, y, bw;

    public GuiAltManager(GuiScreen parent) {
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        Keyboard.enableRepeatEvents(true);
        bw = Math.min(240, this.width - 80);
        int bh = 24, gap = 6;
        cx = this.width / 2;
        y = this.height / 2 - 50;
        cardW = bw + 40;
        cardX = cx - cardW / 2;
        cardY = y - 40;
        cardH = 4 * (bh + gap) + 90;

        nameField = new GuiTextField(0, this.fontRendererObj, cx - bw / 2 + 8, y + 16, bw - 16, 14);
        nameField.setMaxStringLength(16);
        nameField.setFocused(true);
        nameField.setEnableBackgroundDrawing(false);
        nameField.setTextColor(Theme.TEXT);

        this.buttonList.add(new UiButton(1, cx - bw / 2, y + 50,             bw, bh, "Login (Offline)").style(UiButton.PRIMARY).delay(60));
        this.buttonList.add(new UiButton(2, cx - bw / 2, y + 50 + bh + gap,   bw, bh, "Generate Random Alt").delay(100));
        this.buttonList.add(new UiButton(3, cx - bw / 2, y + 50 + 2*(bh+gap), bw, bh, "Back").style(UiButton.DANGER).delay(140));
    }

    @Override
    public void onGuiClosed() { Keyboard.enableRepeatEvents(false); }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: login(nameField.getText()); break;
            case 2:
                String rnd = "KBAlt_" + (1000 + new java.util.Random().nextInt(9000));
                nameField.setText(rnd);
                login(rnd);
                break;
            case 3: closeTo(parent); break;
        }
    }

    private void login(String name) {
        if (name == null || name.trim().isEmpty()) {
            status = "Username cannot be empty!";
            statusColor = Theme.BAD;
            return;
        }
        try {
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
        Draw.rect(0, 0, this.width, this.height, Theme.BG0);
        Draw.panel(cardX, cardY, cardW, cardH, 10f, Theme.SURFACE, Theme.BORDER);

        Draw.centered("ALT MANAGER", cx, cardY + 20, Theme.TEXT, 1.4f, false);
        Draw.centered("Current: " + this.mc.getSession().getUsername(), cx, cardY + 40, Theme.ACCENT, 0.85f, false);

        Draw.roundRect(cx - bw / 2f, y + 10, bw, 24, 5f, Theme.SURFACE2);
        Draw.roundOutline(cx - bw / 2f, y + 10, bw, 24, 5f, 1f,
                nameField.isFocused() ? Theme.ACCENT : Theme.BORDER);
        nameField.drawTextBox();

        Draw.centered(status, cx, cardY + cardH - 16, statusColor, 0.85f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
