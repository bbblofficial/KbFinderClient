package com.oryvex.kbclient;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.GlStateManager;
import org.lwjgl.opengl.GL11;

/** Added by fixer.py - keeps OpenGL state sane so the screen never stays black. */
public final class GlSafe {
    private GlSafe() {}

    public static void push() {
        try { GL11.glPushAttrib(GL11.GL_ALL_ATTRIB_BITS); } catch (Throwable ignored) {}
    }

    public static void pop() {
        try { GL11.glPopAttrib(); } catch (Throwable ignored) {}
        reset();
    }

    public static void reset() {
        try {
            Minecraft mc = Minecraft.getMinecraft();
            if (mc != null && mc.theWorld == null && mc.getFramebuffer() != null) {
                mc.getFramebuffer().bindFramebuffer(true);
            }
            GL11.glDisable(GL11.GL_SCISSOR_TEST);
            GlStateManager.colorMask(true, true, true, true);
            GlStateManager.enableTexture2D();
            GlStateManager.disableLighting();
            GlStateManager.enableAlpha();
            GlStateManager.enableBlend();
            GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
            GlStateManager.color(1.0F, 1.0F, 1.0F, 1.0F);
        } catch (Throwable ignored) {}
    }
}
