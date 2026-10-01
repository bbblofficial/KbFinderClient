package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import org.lwjgl.opengl.GL11;

public final class Draw {
    private Draw() {}

    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }

    public static int lerp(int a, int b, float t) {
        t = clamp(t);
        int aa = (a >>> 24) & 255, ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
        int ba = (b >>> 24) & 255, br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;
        return (((int) (aa + (ba - aa) * t)) << 24) | (((int) (ar + (br - ar) * t)) << 16) | (((int) (ag + (bg - ag) * t)) << 8) | ((int) (ab + (bb - ab) * t));
    }

    public static int alpha(int color, float a) {
        return ((int) (clamp(a) * 255f) << 24) | (color & 0xFFFFFF);
    }

    public static int fade(int color, float a) {
        return ((int) (((color >>> 24) & 255) * clamp(a)) << 24) | (color & 0xFFFFFF);
    }

    public static int confColor(double c) {
        float f = (float) Math.max(0, Math.min(1, c));
        return f < 0.5f ? lerp(Theme.BAD, Theme.WARN, f * 2f) : lerp(Theme.WARN, Theme.GOOD, (f - 0.5f) * 2f);
    }

    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void rect(float x, float y, float w, float h, int color) {
        Gui.drawRect((int)x, (int)y, (int)(x + w), (int)(y + h), color);
    }

    public static void vgradient(int w, int h, int top, int bottom) {
        for (int y = 0; y < h; y += 3) {
            Gui.drawRect(0, y, w, Math.min(h, y + 3), lerp(top, bottom, y / (float) h));
        }
    }

    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        GlStateManager.enableBlend();
        GlStateManager.disableTexture2D();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_POLYGON);
        for (int i = 180; i <= 270; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 270; i <= 360; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 0; i <= 90; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 90; i <= 180; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        GL11.glEnd();

        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void shadow(float x, float y, float w, float h, float r, int color, float spread) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        GlStateManager.enableBlend();
        GlStateManager.disableTexture2D();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(1.5f);

        for (float i = 0.5f; i < spread; i += 0.5f) {
            float a = alpha * (1f - (i / spread)) * 0.05f; 
            GlStateManager.color(red, green, blue, a);
            float nx = x - i, ny = y - i, nw = w + i * 2, nh = h + i * 2, nr = r + i;
            
            GL11.glBegin(GL11.GL_LINE_LOOP);
            for (int j = 180; j <= 270; j += 10) GL11.glVertex2d(nx + nr + Math.cos(Math.toRadians(j)) * nr, ny + nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 270; j <= 360; j += 10) GL11.glVertex2d(nx + nw - nr + Math.cos(Math.toRadians(j)) * nr, ny + nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 0; j <= 90; j += 10) GL11.glVertex2d(nx + nw - nr + Math.cos(Math.toRadians(j)) * nr, ny + nh - nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 90; j <= 180; j += 10) GL11.glVertex2d(nx + nr + Math.cos(Math.toRadians(j)) * nr, ny + nh - nr + Math.sin(Math.toRadians(j)) * nr);
            GL11.glEnd();
        }
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void panel(float x, float y, float w, float h, float r, int fill, int border) {
        shadow(x, y, w, h, r, 0xFF000000, 8f);
        roundRect(x, y, w, h, r, fill);
        if (border != 0) {
            roundRect(x - 0.5f, y - 0.5f, w + 1f, h + 1f, r + 0.5f, border);
            roundRect(x, y, w, h, r, fill);
        }
    }

    public static void bar(float x, float y, float w, float h, double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2f, bg);
        float fw = (float) (w * Math.max(0, Math.min(1, frac)));
        if (fw > 0) {
            shadow(x, y, fw, h, h / 2f, fg, 4f);
            roundRect(x, y, fw, h, h / 2f, fg);
        }
    }

    public static void dashedH(float x, float y, float w, int color) {
        for (int i = 0; i < w; i += 6) rect(x + i, y, Math.min(w - i, 3), 1, color);
    }

    public static void gear(float cx, float cy, float r, float angle, int color, int hole) {
        GlStateManager.pushMatrix();
        GlStateManager.translate(cx, cy, 0f);
        GlStateManager.rotate(angle, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        GlStateManager.rotate(90f, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        GlStateManager.rotate(45f, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        GlStateManager.rotate(90f, 0f, 0f, 1f);
        roundRect(-r, -r/3f, r*2f, r/1.5f, 1f, color);
        roundRect(-r*0.75f, -r*0.75f, r*1.5f, r*1.5f, r*0.75f, color);
        roundRect(-r*0.35f, -r*0.35f, r*0.7f, r*0.7f, r*0.35f, hole);
        GlStateManager.popMatrix();
    }

    public static FontRenderer font() { return Minecraft.getMinecraft().fontRendererObj; }
    public static int width(String s, float scale) { return (int) (font().getStringWidth(s) * scale); }

    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, shadow);
        GlStateManager.popMatrix();
    }

    public static void centered(String s, float cx, float y, int color, float scale, boolean shadow) {
        text(s, cx - font().getStringWidth(s) * scale / 2f, y, color, scale, shadow);
    }

    public static void right(String s, float rx, float y, int color, float scale, boolean shadow) {
        text(s, rx - font().getStringWidth(s) * scale, y, color, scale, shadow);
    }

    /** Premium LiquidBounce/Rise Plexus Effect */
    public static void plexusBackground(int w, int h, float maxAlpha) {
        float t = (System.currentTimeMillis() % 100000L) / 1000f;
        int count = 65;
        float[] px = new float[count];
        float[] py = new float[count];
        
        for (int i = 0; i < count; i++) {
            float sp = 2f + (i % 4) * 1.2f;
            px[i] = (i * 93 + t * sp * 18f) % (w + 100) - 50;
            py[i] = (i * 61 - t * sp * 12f) % (h + 100) - 50;
            if (py[i] < -50) py[i] += h + 100;
        }

        blend();
        GL11.glDisable(GL11.GL_TEXTURE_2D);
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(1.0f);
        
        // Draw Connecting Lines
        GL11.glBegin(GL11.GL_LINES);
        for (int i = 0; i < count; i++) {
            for (int j = i + 1; j < count; j++) {
                float dx = px[i] - px[j];
                float dy = py[i] - py[j];
                float dist = (float) Math.sqrt(dx * dx + dy * dy);
                if (dist < 90f) {
                    float a = (1f - dist / 90f) * maxAlpha * 0.5f;
                    int color = alpha(Theme.ACCENT, a);
                    float red = (color >> 16 & 0xFF) / 255.0F;
                    float green = (color >> 8 & 0xFF) / 255.0F;
                    float blue = (color & 0xFF) / 255.0F;
                    GlStateManager.color(red, green, blue, a);
                    GL11.glVertex2d(px[i], py[i]);
                    GL11.glVertex2d(px[j], py[j]);
                }
            }
        }
        GL11.glEnd();

        // Draw Nodes
        for (int i = 0; i < count; i++) {
            float tw = 0.5f + 0.5f * (float) Math.sin(t * 2f + i);
            int a = (int) (maxAlpha * 255f * tw);
            roundRect(px[i] - 1.5f, py[i] - 1.5f, 3f, 3f, 1.5f, (a << 24) | (Theme.ACCENT & 0xFFFFFF));
        }
        
        GL11.glEnable(GL11.GL_TEXTURE_2D);
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
    }
}
