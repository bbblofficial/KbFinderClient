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
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
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

    private static final int FONT_SIZE   = 32;
    private static final int BASE_HEIGHT = 9;
    private static final int PAD         = 2;

    private static final int[] COLOR_CODES = new int[32];
    static {
        for (int i = 0; i < 32; ++i) {
            int j = (i >> 3 & 1) * 85;
            int k = (i >> 2 & 1) * 170 + j;
            int l = (i >> 1 & 1) * 170 + j;
            int m = (i & 1) * 170 + j;
            if (i == 6) k += 85;
            if (i >= 16) { k /= 4; l /= 4; m /= 4; }
            COLOR_CODES[i] = (k & 255) << 16 | (l & 255) << 8 | m & 255;
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
                try { GlStateManager.deleteTexture(eldest.getValue().id); } catch (Throwable ignored) {}
                return true;
            }
            return false;
        }
    };

    public ModernFontRenderer(GameSettings gs, ResourceLocation loc, TextureManager tm, boolean unicode) {
        super(gs, loc, tm, unicode);
        Font i = load("/fonts/Inter-Regular.ttf");
        Font v = load("/fonts/Vazirmatn-Regular.ttf");
        this.inter = (i != null) ? i : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.vazir = (v != null) ? v : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.FONT_HEIGHT = BASE_HEIGHT;
    }

    private Font load(String path) {
        try {
            InputStream is = ModernFontRenderer.class.getResourceAsStream(path);
            if (is == null) return null;
            Font f = Font.createFont(Font.TRUETYPE_FONT, is).deriveFont((float) FONT_SIZE);
            is.close();
            return f;
        } catch (Throwable t) { return null; }
    }

    public static boolean hasRtl(String text) {
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if ((c >= 0x0590 && c <= 0x05FF)
             || (c >= 0x0600 && c <= 0x06FF)
             || (c >= 0x0750 && c <= 0x077F)
             || (c >= 0x08A0 && c <= 0x08FF)
             || (c >= 0xFB1D && c <= 0xFDFF)
             || (c >= 0xFE70 && c <= 0xFEFF)) return true;
        }
        return false;
    }

    private GlyphTex bake(String text) {
        Font font = hasRtl(text) ? vazir : inter;
        TextLayout layout = new TextLayout(text, font, frc);

        int ascent  = (int) Math.ceil(layout.getAscent());
        int descent = (int) Math.ceil(layout.getDescent());
        int leading = (int) Math.ceil(layout.getLeading());

        Rectangle2D bounds = layout.getBounds();
        int naturalW = (int) Math.ceil(Math.max(bounds.getWidth(), layout.getAdvance()));

        int w = Math.max(1, naturalW + PAD * 2);
        int h = Math.max(1, ascent + descent + leading + PAD * 2);
        int baseline = PAD + ascent;

        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,      RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL,    RenderingHints.VALUE_STROKE_PURE);
        g.setColor(Color.WHITE);
        layout.draw(g, PAD, baseline);
        g.dispose();

        int id = TextureUtil.glGenTextures();
        TextureUtil.uploadTextureImageAllocate(id, img, true, false);

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
            int j = i;
            while (j < n && text.charAt(j) != '\u00a7') j++;
            String piece = text.substring(i, j);
            i = j;
            if (piece.isEmpty()) continue;

            GlyphTex tex = cache.get(piece);
            if (tex == null) { tex = bake(piece); cache.put(piece, tex); }

            GlStateManager.bindTexture(tex.id);
            float r = (curColor >> 16 & 255) / 255f;
            float g = (curColor >> 8  & 255) / 255f;
            float b = ( curColor       & 255) / 255f;
            float a = (curColor >>> 24      ) / 255f;
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
            wr.pos(dx,      dy + dh, 0.0D).tex(0.0D, 1.0D).endVertex();
            wr.pos(dx + dw, dy + dh, 0.0D).tex(1.0D, 1.0D).endVertex();
            wr.pos(dx + dw, dy,      0.0D).tex(1.0D, 0.0D).endVertex();
            wr.pos(dx,      dy,      0.0D).tex(0.0D, 0.0D).endVertex();
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
            if (tex == null) { tex = bake(piece); cache.put(piece, tex); }
            w += tex.width * tex.scale;
        }
        return (int) Math.ceil(w);
    }

    @Override
    public int getCharWidth(char c) {
        if (c == '\u00a7') return -1;
        return getStringWidth(String.valueOf(c));
    }

    @Override
    public boolean getUnicodeFlag() { return false; }

    @Override
    public String trimStringToWidth(String text, int width) {
        return trimStringToWidth(text, width, false);
    }

    @Override
    public String trimStringToWidth(String text, int width, boolean reverse) {
        if (text == null || text.isEmpty()) return "";
        StringBuilder out = new StringBuilder();
        float w = 0;
        int i = reverse ? text.length() - 1 : 0;
        int step = reverse ? -1 : 1;
        while (i >= 0 && i < text.length()) {
            char c = text.charAt(i);
            if (c == '\u00a7' && i + step >= 0 && i + step < text.length()) {
                out.append(c).append(text.charAt(i + step));
                i += step * 2;
                continue;
            }
            float cw = getStringWidth(String.valueOf(c));
            if (w + cw > width) break;
            out.append(c);
            w += cw;
            i += step;
        }
        if (reverse) out.reverse();
        return out.toString();
    }

    @Override
    public List<String> listFormattedStringToWidth(String text, int width) {
        List<String> out = new ArrayList<String>();
        if (text == null || text.isEmpty()) return out;
        String[] lines = text.split("\n", -1);
        for (String line : lines) out.addAll(wrapFormattedStringToWidth(line, width));
        return out;
    }

    private List<String> wrapFormattedStringToWidth(String s, int width) {
        List<String> out = new ArrayList<String>();
        if (s == null || s.isEmpty()) { out.add(""); return out; }
        StringBuilder line = new StringBuilder();
        float w = 0;
        int i = 0;
        while (i < s.length()) {
            char c = s.charAt(i);
            if (c == '\u00a7' && i + 1 < s.length()) {
                line.append(c).append(s.charAt(i + 1));
                i += 2;
                continue;
            }
            if (c == ' ') {
                float sw = getStringWidth(" ");
                if (w + sw > width) { out.add(line.toString()); line.setLength(0); w = 0; }
                else { line.append(c); w += sw; }
                i++;
                continue;
            }
            int j = i;
            while (j < s.length() && s.charAt(j) != ' ' && s.charAt(j) != '\u00a7') j++;
            String word = s.substring(i, j);
            float ww = getStringWidth(word);
            if (w + ww > width && line.length() > 0) { out.add(line.toString()); line.setLength(0); w = 0; }
            line.append(word);
            w += ww;
            i = j;
        }
        if (line.length() > 0) out.add(line.toString());
        return out;
    }

    @Override
    public void onResourceManagerReload(net.minecraft.client.resources.IResourceManager rm) { }
}
