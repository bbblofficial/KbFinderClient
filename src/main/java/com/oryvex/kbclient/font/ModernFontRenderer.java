package com.oryvex.kbclient.font;

import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.Tessellator;
import net.minecraft.client.renderer.WorldRenderer;
import net.minecraft.client.renderer.texture.TextureManager;
import net.minecraft.client.renderer.texture.TextureUtil;
import net.minecraft.client.renderer.vertex.DefaultVertexFormats;
import net.minecraft.client.settings.GameSettings;
import net.minecraft.util.ResourceLocation;

public class ModernFontRenderer extends FontRenderer {
    private Font inter, vazir;
    private final int FONT_SIZE = 48; // Rendered at high-res internally, scaled dynamically
    
    // Custom color map to bypass Minecraft's private colorCode field
    private static final int[] CUSTOM_COLOR_CODES = new int[32];
    static {
        for (int i = 0; i < 32; ++i) {
            int j = (i >> 3 & 1) * 85;
            int k = (i >> 2 & 1) * 170 + j;
            int l = (i >> 1 & 1) * 170 + j;
            int i1 = (i >> 0 & 1) * 170 + j;
            if (i == 6) k += 85;
            if (i >= 16) { k /= 4; l /= 4; i1 /= 4; }
            CUSTOM_COLOR_CODES[i] = (k & 255) << 16 | (l & 255) << 8 | i1 & 255;
        }
    }

    private static class StringTexture {
        int id, width, height;
        float scale;
        StringTexture(int id, int width, int height, float scale) {
            this.id = id; this.width = width; this.height = height; this.scale = scale;
        }
        void delete() {
            GlStateManager.deleteTexture(id);
        }
    }
    
    private final LinkedHashMap<String, StringTexture> cache = new LinkedHashMap<String, StringTexture>(1000, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, StringTexture> eldest) {
            if (size() > 1000) {
                eldest.getValue().delete();
                return true;
            }
            return false;
        }
    };

    public ModernFontRenderer(GameSettings gameSettingsIn, ResourceLocation location, TextureManager textureManagerIn, boolean unicode) {
        super(gameSettingsIn, location, textureManagerIn, unicode);
        inter = loadFont("/fonts/Inter-Regular.ttf", FONT_SIZE);
        vazir = loadFont("/fonts/Vazirmatn-Regular.ttf", FONT_SIZE);
        if (inter == null) inter = new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        if (vazir == null) vazir = new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.FONT_HEIGHT = 9; // Forces vanilla layout compatibility 
    }

    private Font loadFont(String path, float size) {
        try {
            InputStream is = ModernFontRenderer.class.getResourceAsStream(path);
            if (is != null) {
                Font f = Font.createFont(Font.TRUETYPE_FONT, is).deriveFont(size);
                is.close();
                return f;
            }
        } catch (Exception e) {}
        return null;
    }

    private boolean hasPersian(String text) {
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if ((c >= 0x0600 && c <= 0x06FF) || (c >= 0x0750 && c <= 0x077F) || 
                (c >= 0x08A0 && c <= 0x08FF) || (c >= 0xFB50 && c <= 0xFDFF) || 
                (c >= 0xFE70 && c <= 0xFEFF)) return true;
        }
        return false;
    }

    private StringTexture createTexture(String text) {
        Font font = hasPersian(text) ? vazir : inter;
        
        BufferedImage img = new BufferedImage(1, 1, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setFont(font);
        FontMetrics fm = g.getFontMetrics();
        int w = fm.stringWidth(text);
        int h = fm.getHeight();
        g.dispose();
        
        if (w <= 0) w = 1;
        if (h <= 0) h = 1;
        
        img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setFont(font);
        g.setColor(Color.WHITE);
        g.drawString(text, 0, fm.getAscent());
        g.dispose();
        
        int id = TextureUtil.glGenTextures();
        TextureUtil.uploadTextureImageAllocate(id, img, true, false);
        
        // Dynamically calculate the precise scale needed to perfectly match Minecraft's 9px font height
        float scale = (float) this.FONT_HEIGHT / h;
        return new StringTexture(id, w, h, scale);
    }

    @Override
    public int drawString(String text, float x, float y, int color, boolean dropShadow) {
        if (text == null || text.isEmpty()) return (int) x;
        if (dropShadow) renderText(text, x + 0.6f, y + 0.6f, color, true);
        return renderText(text, x, y, color, false);
    }

    private int renderText(String text, float x, float y, int color, boolean shadow) {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.enableTexture2D();
        
        float currentX = x;
        String[] parts = text.split("(?=§)");
        
        int currentColor = color;
        if ((currentColor & 0xFC000000) == 0) currentColor |= 0xFF000000;
        if (shadow) currentColor = (currentColor & 16579836) >> 2 | currentColor & -16777216;

        for (String part : parts) {
            if (part.isEmpty()) continue;
            if (part.startsWith("§")) {
                if (part.length() > 1) {
                    char code = part.charAt(1);
                    int colorIndex = "0123456789abcdef".indexOf(Character.toLowerCase(code));
                    if (colorIndex >= 0) {
                        currentColor = CUSTOM_COLOR_CODES[colorIndex];
                        if (shadow) {
                            currentColor = (currentColor & 16579836) >> 2 | currentColor & -16777216;
                        } else {
                            currentColor |= 0xFF000000;
                        }
                    } else if (code == 'r' || code == 'R') {
                        currentColor = color;
                        if (shadow) currentColor = (currentColor & 16579836) >> 2 | currentColor & -16777216;
                    }
                }
                part = part.substring(2);
            }
            if (part.isEmpty()) continue;
            
            StringTexture tex = cache.get(part);
            if (tex == null) {
                tex = createTexture(part);
                cache.put(part, tex);
            }
            
            GlStateManager.bindTexture(tex.id);
            float r = (currentColor >> 16 & 255) / 255.0F;
            float g = (currentColor >> 8 & 255) / 255.0F;
            float b = (currentColor & 255) / 255.0F;
            float a = (currentColor >> 24 & 255) / 255.0F;
            GlStateManager.color(r, g, b, a);
            
            float scale = tex.scale;
            float drawX = currentX / scale;
            float drawY = y / scale;
            
            GlStateManager.pushMatrix();
            GlStateManager.scale(scale, scale, 1.0f);
            
            Tessellator tessellator = Tessellator.getInstance();
            WorldRenderer worldrenderer = tessellator.getWorldRenderer();
            worldrenderer.begin(7, DefaultVertexFormats.POSITION_TEX);
            worldrenderer.pos(drawX, drawY + tex.height, 0.0D).tex(0.0D, 1.0D).endVertex();
            worldrenderer.pos(drawX + tex.width, drawY + tex.height, 0.0D).tex(1.0D, 1.0D).endVertex();
            worldrenderer.pos(drawX + tex.width, drawY, 0.0D).tex(1.0D, 0.0D).endVertex();
            worldrenderer.pos(drawX, drawY, 0.0D).tex(0.0D, 0.0D).endVertex();
            tessellator.draw();
            
            GlStateManager.popMatrix();
            currentX += tex.width * scale;
        }
        
        GlStateManager.color(1.0F, 1.0F, 1.0F, 1.0F);
        return (int) currentX;
    }

    @Override
    public int getStringWidth(String text) {
        if (text == null || text.isEmpty()) return 0;
        float width = 0;
        String[] parts = text.split("(?=§)");
        for (String part : parts) {
            if (part.startsWith("§") && part.length() > 1) part = part.substring(2);
            if (part.isEmpty()) continue;
            
            StringTexture tex = cache.get(part);
            if (tex == null) {
                tex = createTexture(part);
                cache.put(part, tex);
            }
            width += tex.width * tex.scale;
        }
        return (int) Math.ceil(width);
    }

    @Override
    public int getCharWidth(char character) {
        return getStringWidth(String.valueOf(character));
    }
}
