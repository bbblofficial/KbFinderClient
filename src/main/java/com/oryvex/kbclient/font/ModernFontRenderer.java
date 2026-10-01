package com.oryvex.kbclient.font;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.font.FontRenderContext;
import java.awt.font.TextLayout;
import java.awt.geom.Rectangle2D;
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

/**
 * Replaces Minecraft's font renderer with an AWT-backed one that:
 *   - uses TextLayout for correct Arabic/Persian shaping and BiDi (RTL),
 *   - measures and draws with the exact same scale so layout never drifts,
 *   - falls back to SansSerif if the bundled TTFs cannot be loaded.
 *
 * Added by fixer.py.
 */
public class ModernFontRenderer extends FontRenderer {

    /** Internal raster size — higher = crisper, slower to build the atlas. */
    private static final int FONT_SIZE = 32;
    /** On-screen line height (vanilla default). */
    private static final int BASE_HEIGHT = 9;

    // Vanilla colour-code table (the field itself is private).
    private static final int[] COLOR_CODES = new int[32];
    static {
        for (int i = 0; i < 32; ++i) {
            int j = (i >> 3 & 1) * 85;
            int k = (i >> 2 & 1) * 170 + j;
            int l = (i >> 1 & 1) * 170 + j;
            int i1 = (i >> 0 & 1) * 170 + j;
            if (i == 6) k += 85;
            if (i >= 16) { k /= 4; l /= 4; i1 /= 4; }
            COLOR_CODES[i] = (k & 255) << 16 | (l & 255) << 8 | i1 & 255;
        }
    }

    private final Font inter;
    private final Font vazir;
    private final FontRenderContext frc = new FontRenderContext(null, true, true);

    private static final class GlyphTex {
        final int id, width, height;
        final float scale;
        GlyphTex(int id, int w, int h, float s) { this.id = id; this.width = w; this.height = h; this.scale = s; }
    }

    private final Map<String, GlyphTex> cache = new LinkedHashMap<String, GlyphTex>(512, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, GlyphTex> eldest) {
            if (size() > 512) {
                GlStateManager.deleteTexture(eldest.getValue().id);
                return true;
            }
            return false;
        }
    };

    public ModernFontRenderer(GameSettings gs, ResourceLocation loc, TextureManager tm, boolean unicode) {
        super(gs, loc, tm, unicode);
        Font i = load("/fonts/Inter-Regular.ttf");
        Font v = load("/fonts/Vazirmatn-Regular.ttf");
        inter = (i != null) ? i : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        vazir = (v != null) ? v : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.FONT_HEIGHT = BASE_HEIGHT;
    }

    private Font load(String path) {
        try {
            InputStream is = ModernFontRenderer.class.getResourceAsStream(path);
            if (is == null) return null;
            Font f = Font.createFont(Font.TRUETYPE_FONT, is).deriveFont((float) FONT_SIZE);
            is.close();
            return f;
        } catch (Throwable t) {
            return null;
        }
    }

    /** True if the string contains Arabic / Persian / Hebrew code-points. */
    public static boolean hasRtl(String text) {
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if ((c >= 0x0590 && c <= 0x05FF)   // Hebrew
             || (c >= 0x0600 && c <= 0x06FF)   // Arabic
             || (c >= 0x0750 && c <= 0x077F)
             || (c >= 0x08A0 && c <= 0x08FF)
             || (c >= 0xFB1D && c <= 0xFDFF)
             || (c >= 0xFE70 && c <= 0xFEFF)) return true;
        }
        return false;
    }

    private GlyphTex bake(String text) {
        Font font = hasRtl(text) ? vazir : inter;

        // TextLayout performs Arabic/Persian shaping + BiDi reordering.
        TextLayout layout = new TextLayout(text, font, frc);
        Rectangle2D bounds = layout.getBounds();
        int pad = 2;
        int w = Math.max(1, (int) Math.ceil(bounds.getWidth()) + pad * 2);
        int h = Math.max(1, (int) Math.ceil(bounds.getHeight()) + pad * 2);
        int baseline = (int) Math.ceil(layout.getAscent()) + pad;

        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setColor(Color.WHITE);
        layout.draw(g, pad, baseline);
        g.dispose();

        int id = TextureUtil.glGenTextures();
        TextureUtil.uploadTextureImageAllocate(id, img, true, false);

        // FONT_SIZE raster -> BASE_HEIGHT on screen.
        float scale = (float) BASE_HEIGHT / FONT_SIZE;
        return new GlyphTex(id, w, h, scale);
    }

    @Override
    public int drawString(String text, float x, float y, int color, boolean dropShadow) {
        if (text == null || text.isEmpty()) return (int) x;
        if (dropShadow) draw(text, x + 1f, y + 1f, color, true);
        return draw(text, x, y, color, false);
    }

    @Override
    public int drawStringWithShadow(String text, float x, float y, int color) {
        return drawString(text, x, y, color, true);
    }

    private int draw(String text, float x, float y, int color, boolean shadow) {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.enableTexture2D();

        float curX = x;
        int curColor = color;
        if ((curColor & 0xFC000000) == 0) curColor |= 0xFF000000;
        if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000);

        // Split on formatting codes so colours don't bleed into each glyph.
        int i = 0;
        final int n = text.length();
        while (i < n) {
            if (text.charAt(i) == '\u00a7' && i + 1 < n) {
                char code = Character.toLowerCase(text.charAt(i + 1));
                int ci = "0123456789abcdef".indexOf(code);
                if (ci >= 0) {
                    curColor = COLOR_CODES[ci];
                    if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000);
                    else curColor |= 0xFF000000;
                } else if (code == 'r') {
                    curColor = color;
                    if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000);
                }
                i += 2;
                continue;
            }
            // take until next §
            int j = i;
            while (j < n && text.charAt(j) != '\u00a7') j++;
            String piece = text.substring(i, j);
            i = j;
            if (piece.isEmpty()) continue;

            GlyphTex tex = cache.get(piece);
            if (tex == null) {
                tex = bake(piece);
                cache.put(piece, tex);
            }

            GlStateManager.bindTexture(tex.id);
            float r = (curColor >> 16 & 255) / 255f;
            float g = (curColor >> 8 & 255) / 255f;
            float b = (curColor & 255) / 255f;
            float a = (curColor >>> 24) / 255f;
            GlStateManager.color(r, g, b, a);

            float s = tex.scale;
            GlStateManager.pushMatrix();
            GlStateManager.scale(s, s, 1f);

            float dx = curX / s;
            float dy = y / s;
            float dw = tex.width;
            float dh = tex.height;

            Tessellator t = Tessellator.getInstance();
            WorldRenderer wr = t.getWorldRenderer();
            wr.begin(7, DefaultVertexFormats.POSITION_TEX);
            wr.pos(dx,     dy + dh, 0.0D).tex(0.0D, 1.0D).endVertex();
            wr.pos(dx + dw, dy + dh, 0.0D).tex(1.0D, 1.0D).endVertex();
            wr.pos(dx + dw, dy,     0.0D).tex(1.0D, 0.0D).endVertex();
            wr.pos(dx,     dy,      0.0D).tex(0.0D, 0.0D).endVertex();
            t.draw();

            GlStateManager.popMatrix();
            curX += tex.width * s;
        }

        GlStateManager.color(1f, 1f, 1f, 1f);
        return (int) curX;
    }

    @Override
    public int getStringWidth(String text) {
        if (text == null || text.isEmpty()) return 0;
        float w = 0;
        int i = 0;
        final int n = text.length();
        while (i < n) {
            if (text.charAt(i) == '\u00a7' && i + 1 < n) { i += 2; continue; }
            int j = i;
            while (j < n && text.charAt(j) != '\u00a7') j++;
            String piece = text.substring(i, j);
            i = j;
            if (piece.isEmpty()) continue;
            GlyphTex tex = cache.get(piece);
            if (tex == null) {
                tex = bake(piece);
                cache.put(piece, tex);
            }
            w += tex.width * tex.scale;
        }
        return (int) Math.ceil(w);
    }

    @Override
    public int getCharWidth(char character) {
        if (character == '\u00a7') return -1;
        return getStringWidth(String.valueOf(character));
    }

    @Override
    public boolean getUnicodeFlag() { return false; }

    @Override
    public void onResourceManagerReload(net.minecraft.client.resources.IResourceManager rm) {
        // Keep our custom fonts after a resource reload.
    }
}
