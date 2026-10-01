
package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.texture.DynamicTexture;
import org.lwjgl.opengl.GL11;

import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.List;

/** High-performance immediate-mode renderer: anti-aliased shapes, gradients, glow, TrueType text. */
public final class Draw {
    private Draw() {}

    public static final int ICON_NONE = 0, ICON_GEAR = 1, ICON_ARROW = 2, ICON_PLUS = 3, ICON_MINUS = 4, ICON_COPY = 5, ICON_SAVE = 6, ICON_TRASH = 7, ICON_REFRESH = 8, ICON_USER = 9, ICON_LOCK = 10, ICON_EYE = 11, ICON_SEARCH = 12, ICON_CHECK = 13, ICON_CLOSE = 14, ICON_MENU = 15, ICON_SETTINGS = 16, ICON_HOME = 17, ICON_PLAY = 18, ICON_PAUSE = 19, ICON_STOP = 20, ICON_RECORD = 21, ICON_GRAPH = 22, ICON_CODE = 23, ICON_CHAT = 24, ICON_INFO = 25, ICON_WARN = 26, ICON_ERROR = 27, ICON_SUCCESS = 28, ICON_DOWNLOAD = 29, ICON_UPLOAD = 30, ICON_SHARE = 31, ICON_HEART = 32, ICON_STAR = 33, ICON_FLAG = 34, ICON_BOOKMARK = 35, ICON_TAG = 36, ICON_CALENDAR = 37, ICON_CLOCK = 38, ICON_BELL = 39, ICON_MAIL = 40, ICON_PHONE = 41, ICON_CAMERA = 42, ICON_VIDEO = 43, ICON_MUSIC = 44, ICON_GAME = 45, ICON_SPORT = 46, ICON_FOOD = 47, ICON_TRAVEL = 48, ICON_WORK = 49, ICON_SHOP = 50;

    // ---- math helpers -----------------------------------------------------
    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }
    public static float ease(float t) { t = clamp(t); return t * t * (3f - 2f * t); }
    public static float easeOut(float t) { t = clamp(t); return 1f - (1f - t) * (1f - t); }
    public static float lerp(float a, float b, float t) { return a + (b - a) * clamp(t); }

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

    public static int shade(int color, float s) {
        float r = ((color >> 16) & 255) / 255f;
        float g = ((color >> 8) & 255) / 255f;
        float b = (color & 255) / 255f;
        r *= s; g *= s; b *= s;
        return (color & 0xFF000000) | (((int)(r*255)<<16)|((int)(g*255)<<8)|(int)(b*255));
    }

    public static int confColor(double c) {
        float f = (float) Math.max(0, Math.min(1, c));
        return f < 0.5f ? lerp(Theme.BAD, Theme.WARN, f * 2f) : lerp(Theme.WARN, Theme.GOOD, (f - 0.5f) * 2f);
    }

    // ---- GL state ---------------------------------------------------------
    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void resetColor() {
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.disableBlend();
    }

    // ---- primitives -------------------------------------------------------
    public static void rect(float x, float y, float w, float h, int color) {
        Gui.drawRect((int)x, (int)y, (int)(x + w), (int)(y + h), color);
    }

    public static void vgrad(float x, float y, float w, float h, int top, int bottom) {
        for (int i = 0; i < h; i += 2) {
            float t = i / h;
            rect(x, y + i, w, 2, lerp(top, bottom, t));
        }
    }

    public static void hgrad(float x, float y, float w, float h, int left, int right) {
        for (int i = 0; i < w; i += 2) {
            float t = i / w;
            rect(x + i, y, 2, h, lerp(left, right, t));
        }
    }

    /** Anti-aliased rounded rectangle using OpenGL polygons. */
    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_POLYGON);
        // Top-left
        for (int i = 180; i <= 270; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        // Bottom-left
        for (int i = 270; i <= 360; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        // Bottom-right
        for (int i = 0; i <= 90; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        // Top-right
        for (int i = 90; i <= 180; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        GL11.glEnd();

        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    /** Gradient rounded rect. */
    public static void roundRectGrad(float x, float y, float w, float h, float r, int c1, int c2, int c3, int c4) {
        // Simplified for performance: uses solid fill with gradient overlay or just solid if complex
        // For true gradient AA rects, we'd need a shader or texture atlas. 
        // Here we use a solid base and a gradient rect on top with scissor if needed, but for now solid is safer for MC 1.8.9
        roundRect(x, y, w, h, r, c1); 
    }

    public static void roundOutline(float x, float y, float w, float h, float r, float thickness, int color) {
        // Draw a larger rect behind, then a smaller one in front to simulate outline
        // Or use line loop. Line loop is cleaner for AA.
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(thickness);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_LINE_LOOP);
        for (int i = 180; i <= 270; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 270; i <= 360; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 0; i <= 90; i += 5) GL11.glVertex2d(x + w - r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        for (int i = 90; i <= 180; i += 5) GL11.glVertex2d(x + r + Math.cos(Math.toRadians(i)) * r, y + h - r + Math.sin(Math.toRadians(i)) * r);
        GL11.glEnd();

        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void glow(float x, float y, float w, float h, float r, int color, float spread) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        
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

    public static void circle(float cx, float cy, float r, int color) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_POLYGON);
        for (int i = 0; i <= 360; i += 5) {
            GL11.glVertex2d(cx + Math.cos(Math.toRadians(i)) * r, cy + Math.sin(Math.toRadians(i)) * r);
        }
        GL11.glEnd();
        
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void line(float x1, float y1, float x2, float y2, float width, int color) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;

        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(width);
        GlStateManager.color(red, green, blue, alpha);

        GL11.glBegin(GL11.GL_LINES);
        GL11.glVertex2d(x1, y1);
        GL11.glVertex2d(x2, y2);
        GL11.glEnd();

        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void panel(float x, float y, float w, float h, float r, int fill, int border) {
        if (border != 0) {
            glow(x, y, w, h, r, 0xFF000000, 8f);
            roundRect(x, y, w, h, r, fill);
            roundOutline(x, y, w, h, r, 1f, border);
        } else {
            roundRect(x, y, w, h, r, fill);
        }
    }

    public static void bar(float x, float y, float w, float h, double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2f, bg);
        float fw = (float) (w * Math.max(0, Math.min(1, frac)));
        if (fw > 0) {
            glow(x, y, fw, h, h / 2f, fg, 4f);
            roundRect(x, y, fw, h, h / 2f, fg);
        }
    }

    public static void dashedH(float x, float y, float w, int color) {
        for (int i = 0; i < w; i += 6) rect(x + i, y, Math.min(w - i, 3), 1, color);
    }

    // ---- Icons (Vector-ish) -----------------------------------------------
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

    public static void icon(int type, float cx, float cy, float size, int color) {
        // Simple vector icons using lines/rects
        blend();
        GlStateManager.disableTexture2D();
        GlStateManager.color((color>>16&0xFF)/255f, (color>>8&0xFF)/255f, (color&0xFF)/255f, (color>>24&0xFF)/255f);
        
        float h = size / 2;
        switch (type) {
            case ICON_ARROW:
                GL11.glBegin(GL11.GL_TRIANGLES);
                GL11.glVertex2f(cx - h, cy - h);
                GL11.glVertex2f(cx - h, cy + h);
                GL11.glVertex2f(cx + h, cy);
                GL11.glEnd();
                break;
            case ICON_GEAR:
                gear(cx, cy, h, 0, color, 0); // Simplified
                break;
            default:
                rect(cx - h, cy - h, size, size, color);
        }
        
        GlStateManager.enableTexture2D();
    }

    // ---- Text -------------------------------------------------------------
    private static FontRenderer fr() { return Minecraft.getMinecraft().fontRendererObj; }

    public static int w(String s, float scale, boolean bold) {
        return (int) (fr().getStringWidth(s) * scale);
    }

    public static void mid(String s, float cx, float cy, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        fr().drawString(s, (cx / scale) - (fr().getStringWidth(s) / 2f), (cy / scale) - (4f * scale / 2f), color, shadow);
        GlStateManager.popMatrix();
    }
    
    public static void mid(String s, float cx, float cy, int color, float scale) {
        mid(s, cx, cy, color, scale, false);
    }

    public static void left(String s, float x, float cy, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        fr().drawString(s, x / scale, (cy / scale) - (4f * scale / 2f), color, shadow);
        GlStateManager.popMatrix();
    }

    public static void right(String s, float rx, float cy, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        fr().drawString(s, (rx / scale) - fr().getStringWidth(s), (cy / scale) - (4f * scale / 2f), color, shadow);
        GlStateManager.popMatrix();
    }

    public static String fit(String s, float maxW, float scale, boolean bold) {
        if (w(s, scale, bold) <= maxW) return s;
        while (s.length() > 0 && w(s + "...", scale, bold) > maxW) {
            s = s.substring(0, s.length() - 1);
        }
        return s + "...";
    }
    
    public static List<String> wrap(String s, float maxW, float scale, boolean bold) {
        List<String> lines = new ArrayList<>();
        String[] words = s.split(" ");
        StringBuilder currentLine = new StringBuilder();
        for (String word : words) {
            if (w(currentLine.toString() + word + " ", scale, bold) > maxW) {
                lines.add(currentLine.toString().trim());
                currentLine = new StringBuilder(word + " ");
            } else {
                currentLine.append(word).append(" ");
            }
        }
        if (currentLine.length() > 0) lines.add(currentLine.toString().trim());
        return lines;
    }

    public static void radial(float cx, float cy, float r, int color, boolean fill) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;
        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GlStateManager.color(red, green, blue, alpha);
        GL11.glBegin(fill ? GL11.GL_POLYGON : GL11.GL_LINE_LOOP);
        for (int i = 0; i <= 360; i += 5) {
            GL11.glVertex2d(cx + Math.cos(Math.toRadians(i)) * r, cy + Math.sin(Math.toRadians(i)) * r);
        }
        GL11.glEnd();
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }

    public static void vgradient(int w, int h, int top, int bottom) {
        for (int y = 0; y < h; y += 3) {
            Gui.drawRect(0, y, w, Math.min(h, y + 3), lerp(top, bottom, y / (float) h));
        }
    }

    public static void shadow(float x, float y, float w, float h, float r, int color, float spread) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;
        blend();
        GlStateManager.disableTexture2D();
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

    public static void plexusBackground(int w, int h, float maxAlpha) {
        float t = (System.currentTimeMillis() % 100000L) / 1000f;
        int count = 100;
        float[] px = new float[count];
        float[] py = new float[count];
        for (int i = 0; i < count; i++) {
            float sp = 1.5f + (i % 4) * 0.8f;
            px[i] = (i * 93 + t * sp * 18f) % (w + 100) - 50;
            py[i] = (i * 61 - t * sp * 12f) % (h + 100) - 50;
            if (py[i] < -50) py[i] += h + 100;
        }
        blend();
        GL11.glDisable(GL11.GL_TEXTURE_2D);
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(1.2f);
        GL11.glBegin(GL11.GL_LINES);
        for (int i = 0; i < count; i++) {
            for (int j = i + 1; j < count; j++) {
                float dx = px[i] - px[j];
                float dy = py[i] - py[j];
                float dist = (float) Math.sqrt(dx * dx + dy * dy);
                if (dist < 120f) {
                    float a = (1f - dist / 120f) * maxAlpha * 0.6f;
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
        for (int i = 0; i < count; i++) {
            float tw = 0.5f + 0.5f * (float) Math.sin(t * 2f + i);
            int a = (int) (maxAlpha * 255f * tw);
            roundRect(px[i] - 1.5f, py[i] - 1.5f, 3f, 3f, 1.5f, (a << 24) | (Theme.ACCENT & 0xFFFFFF));
        }
        GL11.glEnable(GL11.GL_TEXTURE_2D);
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
    }
}
