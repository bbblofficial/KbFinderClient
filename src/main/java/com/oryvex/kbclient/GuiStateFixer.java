package com.oryvex.kbclient;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiMainMenu;
import net.minecraftforge.client.event.GuiOpenEvent;
import net.minecraftforge.fml.common.eventhandler.EventPriority;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.gameevent.TickEvent;

/** Added by fixer.py - prevents the black screen when returning from Singleplayer. */
public class GuiStateFixer {
    private int blackTicks = 0;

    /** Runs last: if anything turned the next screen into null while no world is loaded, use the main menu. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public void onGuiOpen(GuiOpenEvent e) {
        Minecraft mc = Minecraft.getMinecraft();
        if (e.gui == null && mc.theWorld == null) {
            e.gui = new GuiMainMenu();
        }
        GlSafe.reset();
    }

    /** Safety net: no world + no screen for 3 ticks = black screen -> open the main menu. */
    @SubscribeEvent
    public void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.theWorld == null && mc.currentScreen == null) {
            if (++blackTicks >= 3) {
                blackTicks = 0;
                GlSafe.reset();
                mc.displayGuiScreen(new GuiMainMenu());
            }
        } else {
            blackTicks = 0;
        }
    }

    /** In menus, reset GL state at the end of each frame so a broken overlay can't blacken the screen. */
    @SubscribeEvent
    public void onRenderTick(TickEvent.RenderTickEvent e) {
        if (e.phase == TickEvent.Phase.END && Minecraft.getMinecraft().theWorld == null) {
            GlSafe.reset();
        }
    }
}
