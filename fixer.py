import os
import shutil

# Define the changes to be applied
files_to_modify = {
    "src/main/java/com/oryvex/kbclient/ui/Theme.java": """package com.oryvex.kbclient.ui;
/** Flat colour palette. Simplified for clarity. */
public final class Theme {
    private Theme() {}
    // ---- backgrounds ----
    public static final int BG0   = 0xFF0A0E14;
    public static final int BG1   = 0xFF11161F;
    // ---- surfaces ----
    public static final int SURFACE   = 0xFF161B24;
    public static final int SURFACE2  = 0xFF1D232E;
    public static final int SURFACE3  = 0xFF252C38;
    public static final int BORDER    = 0xFF2A323E;
    public static final int BORDER_HI = 0xFF3A4453;
    // ---- status ----
    public static final int GOOD = 0xFF4ADE80;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD  = 0xFFF87171;
    // ---- text ----
    public static final int TEXT  = 0xFFF1F5F9;
    public static final int SOFT  = 0xFFCBD5E1;
    public static final int MUTED = 0xFF94A3B8;
    public static final int DIM   = 0xFF64748B;
    // ---- accent ----
    public static final int ACCENT    = 0xFF3B82F6;
    public static final int ACCENT_DK = 0xFF1E40AF;
    public static final String S = "\\u00a7";
}""",
    "src/main/java/com/oryvex/kbclient/ui/Draw.java": """package com.oryvex.kbclient.ui;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import java.util.ArrayList;
import java.util.List;
/** Minimal drawing toolkit. Icons removed for simpler design. */
public final class Draw {
    private Draw() {}
    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }
    public static float ease(float t) { t = clamp(t); return t * t * (3f - 2f * t); }
    public static float easeOut(float t) { t = clamp(t); return 1f - (1f - t) * (1f - t); }
    public static int lerp(int a, int b, float t) {
        t = clamp(t);
        int aa = (a >>> 24) & 255, ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
        int ba = (b >>> 24) & 255, br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;
        return (((int)(aa + (ba - aa) * t)) << 24) | (((int)(ar + (br - ar) * t)) << 16) | (((int)(ag + (bg - ag) * t)) << 8) | ((int)(ab + (bb - ab) * t));
    }
    public static int alpha(int color, float a) { return ((int)(clamp(a) * 255f) << 24) | (color & 0xFFFFFF); }
    public static int fade(int color, float a) { return ((int)(((color >>> 24) & 255) * clamp(a)) << 24) | (color & 0xFFFFFF); }
    public static void blend() { GlStateManager.enableBlend(); GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0); GlStateManager.color(1f, 1f, 1f, 1f); }
    public static void rect(float x, float y, float w, float h, int color) { Gui.drawRect((int)x, (int)y, (int)(x + w), (int)(y + h), color); }
    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        if (w <= 0 || h <= 0 || ((color >>> 24) & 255) <= 4) return;
        r = Math.min(r, Math.min(w, h) / 2f);
        int ir = (int) Math.ceil(r);
        if (ir <= 0) { Gui.drawRect((int)x, (int)y, (int)(x+w), (int)(y+h), color); return; }
        Gui.drawRect((int)x, (int)(y + r), (int)(x + w), (int)(y + h - r), color);
        Gui.drawRect((int)(x + r), (int)y, (int)(x + w - r), (int)(y + r), color);
        Gui.drawRect((int)(x + r), (int)(y + h - r), (int)(x + w - r), (int)(y + h), color);
        for (int i = 0; i < ir; i++) {
            double dy = ir - i - 0.5;
            int inset = (int) Math.round(ir - Math.sqrt(Math.max(0, ir * ir - dy * dy)));
            Gui.drawRect((int)(x + inset), (int)(y + i), (int)(x + w - inset), (int)(y + i + 1), color);
            Gui.drawRect((int)(x + inset), (int)(y + h - i - 1), (int)(x + w - inset), (int)(y + h - i), color);
        }
    }
    public static void panel(float x, float y, float w, float h, float r, int fill, int border) {
        if (((fill >>> 24) & 255) > 4) roundRect(x, y, w, h, r, fill);
        if (border != 0 && ((border >>> 24) & 255) > 4) {
            roundRect(x, y, w, h, r, border);
            roundRect(x + 1, y + 1, w - 2, h - 2, Math.max(0, r - 1), fill);
        }
    }
    public static FontRenderer font() {
        try {
            com.oryvex.kbclient.font.ModernFontRenderer mf = com.oryvex.kbclient.KBClientMod.modernFont;
            if (mf != null) return mf;
        } catch (Throwable ignored) { }
        return Minecraft.getMinecraft().fontRendererObj;
    }
    public static int width(String s, float scale) { return (int)(font().getStringWidth(s) * scale); }
    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty() || ((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, false);
        GlStateManager.popMatrix();
    }
    public static void centered(String s, float cx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, cx - tw / 2f, cy - th / 2f, color, scale, false);
    }
    public static void left(String s, float x, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float th = font().FONT_HEIGHT * scale;
        text(s, x, cy - th / 2f, color, scale, false);
    }
    public static void right(String s, float rx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, rx - tw, cy - th / 2f, color, scale, false);
    }
}""",
    "src/main/java/com/oryvex/kbclient/ui/UiButton.java": """package com.oryvex.kbclient.ui;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
/** Simple flat button. No icons, no complex animations. */
public class UiButton extends GuiButton {
    public static final int NORMAL  = 0;
    public static final int PRIMARY = 1;
    public static final int DANGER  = 2;
    public static final int TAB     = 3;
    public static final int TOGGLE  = 4;
    public int style = NORMAL;
    public boolean selected;
    public boolean on;
    public long delay;
    private final Anim hover = new Anim();
    private final long born = System.currentTimeMillis();
    public UiButton(int id, int x, int y, int w, int h, String text) { super(id, x, y, w, h, text); }
    public UiButton style(int s) { this.style = s; return this; }
    public UiButton delay(long d) { this.delay = d; return this; }
    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;
        boolean act = this.hovered && this.enabled;
        float hv = hover.to(act ? 1f : 0f, 22f);
        float ap = Draw.easeOut((System.currentTimeMillis() - born - delay) / 260f);
        if (ap <= 0.01f) return;
        if (!enabled) ap *= 0.5f;
        float x = xPosition;
        float y = yPosition + (1f - ap) * 6f;
        float w = width;
        float h = height;
        float r = 4f;
        float cy = y + h / 2f;
        int bg, border, textCol;
        switch (style) {
            case PRIMARY: bg = Draw.lerp(Theme.ACCENT_DK, Theme.ACCENT, hv); border = Theme.ACCENT; textCol = 0xFFFFFFFF; break;
            case DANGER: bg = Draw.lerp(0x18FB7185, 0x40FB7185, hv); border = Draw.lerp(0x44FB7185, Theme.BAD, hv); textCol = Draw.lerp(0xFFFCA5A5, 0xFFFFFFFF, hv); break;
            case TAB: bg = selected ? Theme.SURFACE2 : Draw.lerp(0x00FFFFFF, Theme.SURFACE2, hv); border = selected ? Theme.BORDER_HI : Theme.BORDER; textCol = selected ? Theme.TEXT : Draw.lerp(Theme.MUTED, Theme.TEXT, hv); break;
            case TOGGLE: bg = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv); border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv); textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv); break;
            default: bg = Draw.lerp(Theme.SURFACE2, Theme.SURFACE3, hv); border = Draw.lerp(Theme.BORDER, Theme.BORDER_HI, hv); textCol = Draw.lerp(Theme.SOFT, Theme.TEXT, hv);
        }
        bg = Draw.fade(bg, ap);
        border = Draw.fade(border, ap);
        textCol = Draw.fade(textCol, ap);
        Draw.panel(x, y, w, h, r, bg, border);
        if (style == TOGGLE) {
            Draw.left(displayString, x + 8f, cy, textCol, 1.0f, false);
            float sw = 22f, sh = 12f;
            float sx = x + w - sw - 8f;
            int track = on ? Theme.ACCENT : 0x30FFFFFF;
            Draw.roundRect(sx, cy - sh/2, sw, sh, sh/2, Draw.fade(track, ap));
            float kx = sx + sh/2 + (sw - sh) * (on ? 1f : 0f);
            Draw.roundRect(kx - sh/2 + 1, cy - sh/2 + 1, sh-2, sh-2, sh/2-1, Draw.fade(0xFFFFFFFF, ap));
            return;
        }
        Draw.centered(displayString, x + w / 2f, cy, textCol, 1.0f, false);
        if (style == TAB && selected) Draw.rect(x + 4f, y + h - 2f, w - 8f, 2f, Theme.ACCENT);
    }
}""",
    "src/main/java/com/oryvex/kbclient/ui/Hud.java": """package com.oryvex.kbclient.ui;
import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBSample;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.ScaledResolution;
public final class Hud {
    private Hud() {}
    private static final class Toast { final String text; final int color; final long born; Toast(String t, int c) { text = t; color = c; born = System.currentTimeMillis(); } }
    private static final List<Toast> toasts = new ArrayList<Toast>();
    private static float alpha = 0f;
    private static long lastNs = System.nanoTime();
    public static void push(String text, int color) { if (!Settings.toasts) return; toasts.add(new Toast(text, color)); while (toasts.size() > 4) toasts.remove(0); }
    public static void render(Minecraft mc, KBTracker t) {
        ScaledResolution res = new ScaledResolution(mc);
        if (Settings.watermark) Draw.right("Created by muvixo", res.getScaledWidth() - 6, res.getScaledHeight() - 10, Theme.DIM, 0.7f, false);
        long ns = System.nanoTime();
        float dt = Math.min(0.1f, (ns - lastNs) / 1.0e9f);
        lastNs = ns;
        alpha += ((Settings.hud ? 1f : 0f) - alpha) * Math.min(1f, dt * 8f);
        if (alpha < 0.03f) return;
        float a = alpha;
        KBProfile pr = t.getProfile();
        KBSample last = t.getLast();
        boolean goal = t.getGoal() > 0;
        int x = 6, y = 6, w = 140;
        int h = goal ? 50 : 42;
        Draw.panel(x, y, w, h, 4, Draw.fade(Theme.SURFACE, a), Draw.fade(Theme.BORDER, a));
        Draw.left("KB CLIENT", x + 8, y + 10, Draw.fade(Theme.TEXT, a), 0.85f, false);
        Draw.right(t.isRecording() ? "REC" : "PAUSED", x + w - 8, y + 10, Draw.fade(t.isRecording() ? Theme.GOOD : Theme.WARN, a), 0.8f, false);
        if (last != null) Draw.left("H " + KBProfile.f(last.h, 4) + " V " + KBProfile.f(last.vy, 4), x + 8, y + 22, Draw.fade(Theme.SOFT, a), 0.85f, false);
        else Draw.left("Waiting...", x + 8, y + 22, Draw.fade(Theme.MUTED, a), 0.85f, false);
        Draw.left(pr.used + " / " + pr.total, x + 8, y + 32, Draw.fade(Theme.MUTED, a), 0.75f, false);
        if (goal) Draw.bar(x + 8, y + h - 8, w - 16, 2, t.getSessionHits() / (double) t.getGoal(), Draw.fade(Theme.SURFACE3, a), Draw.fade(Theme.ACCENT, a));
        long now = System.currentTimeMillis();
        for (int i = toasts.size() - 1; i >= 0; i--) if (now - toasts.get(i).born > 3600) toasts.remove(i);
        int ty = y + h + 4;
        for (int i = toasts.size() - 1; i >= 0; i--) {
            Toast to = toasts.get(i);
            long age = now - to.born;
            float in = age < 160 ? age / 160f : 1f;
            float fade = (age > 2800 ? 1f - (age - 2800) / 800f : 1f) * in * a;
            int tw = Draw.width(to.text, 0.85f) + 12;
            Draw.panel(x, ty, tw, 14, 3, Draw.alpha(Theme.SURFACE, 0.95f * fade), Draw.alpha(Theme.BORDER, fade));
            int al = (int)(255 * fade);
            if (al > 4) Draw.left(to.text, x + 6, ty + 7, (al << 24) | (to.color & 0xFFFFFF), 0.85f, false);
            ty += 16;
        }
    }
}""",
    "src/main/java/com/oryvex/kbclient/font/ModernFontRenderer.java": """package com.oryvex.kbclient.font;
import java.awt.*;
import java.awt.font.*;
import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.client.renderer.Tessellator;
import net.minecraft.client.renderer.WorldRenderer;
import net.minecraft.client.renderer.texture.TextureUtil;
import net.minecraft.client.renderer.vertex.DefaultVertexFormats;
import net.minecraft.client.settings.GameSettings;
import net.minecraft.util.ResourceLocation;
/** AWT-backed font renderer. Simplified for performance and clarity. */
public class ModernFontRenderer extends FontRenderer {
    private static final int FONT_SIZE = 32;
    private static final int BASE_HEIGHT = 9;
    private static final int PAD = 2;
    private static final int[] COLOR_CODES = new int[32];
    static { for (int i = 0; i < 32; ++i) { int j = (i >> 3 & 1) * 85; int k = (i >> 2 & 1) * 170 + j; int l = (i >> 1 & 1) * 170 + j; int m = (i & 1) * 170 + j; if (i == 6) k += 85; if (i >= 16) { k /= 4; l /= 4; m /= 4; } COLOR_CODES[i] = (k & 255) << 16 | (l & 255) << 8 | m & 255; } }
    private final Font inter;
    private final Font vazir;
    private final FontRenderContext frc = new FontRenderContext(null, true, true);
    private static final class GlyphTex { final int id, width, height; final float scale; GlyphTex(int id, int w, int h, float s) { this.id = id; this.width = w; this.height = h; this.scale = s; } }
    private final Map<String, GlyphTex> cache = new LinkedHashMap<String, GlyphTex>(1024, 0.75f, true) { @Override protected boolean removeEldestEntry(Map.Entry<String, GlyphTex> eldest) { if (size() > 1024) { try { GlStateManager.deleteTexture(eldest.getValue().id); } catch (Throwable ignored) {} return true; } return false; } };
    public ModernFontRenderer(GameSettings gs, ResourceLocation loc, net.minecraft.client.renderer.texture.TextureManager tm, boolean unicode) {
        super(gs, loc, tm, unicode);
        Font i = load("/fonts/Inter-Regular.ttf");
        Font v = load("/fonts/Vazirmatn-Regular.ttf");
        this.inter = (i != null) ? i : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.vazir = (v != null) ? v : new Font("SansSerif", Font.PLAIN, FONT_SIZE);
        this.FONT_HEIGHT = BASE_HEIGHT;
    }
    private Font load(String path) { try { InputStream is = ModernFontRenderer.class.getResourceAsStream(path); if (is == null) return null; Font f = Font.createFont(Font.TRUETYPE_FONT, is).deriveFont((float) FONT_SIZE); is.close(); return f; } catch (Throwable t) { return null; } }
    public static boolean hasRtl(String text) { for (int i = 0; i < text.length(); i++) { char c = text.charAt(i); if ((c >= 0x0590 && c <= 0x05FF) || (c >= 0x0600 && c <= 0x06FF) || (c >= 0x0750 && c <= 0x077F) || (c >= 0x08A0 && c <= 0x08FF) || (c >= 0xFB1D && c <= 0xFDFF) || (c >= 0xFE70 && c <= 0xFEFF)) return true; } return false; }
    private GlyphTex bake(String text) {
        Font font = hasRtl(text) ? vazir : inter;
        TextLayout layout = new TextLayout(text, font, frc);
        int ascent = (int) Math.ceil(layout.getAscent());
        int descent = (int) Math.ceil(layout.getDescent());
        int leading = (int) Math.ceil(layout.getLeading());
        Rectangle2D bounds = layout.getBounds();
        int naturalW = (int) Math.ceil(Math.max(bounds.getWidth(), layout.getAdvance()));
        int w = Math.max(1, naturalW + PAD * 2);
        int h = Math.max(1, ascent + descent + leading + PAD * 2);
        int baseline = PAD + ascent;
        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
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
        StringBuilder run = new StringBuilder();
        while (i < n) {
            if (text.charAt(i) == '\\u00a7' && i + 1 < n) {
                if (run.length() > 0) { curX = drawRun(run.toString(), curX, y, curColor); run.setLength(0); }
                char code = Character.toLowerCase(text.charAt(i + 1));
                int ci = "0123456789abcdef".indexOf(code);
                if (ci >= 0) { curColor = COLOR_CODES[ci]; if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000); else curColor |= 0xFF000000; }
                else if (code == 'r') { curColor = color; if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000); }
                i += 2; continue;
            }
            run.append(text.charAt(i)); i++;
        }
        if (run.length() > 0) curX = drawRun(run.toString(), curX, y, curColor);
        GlStateManager.color(1f, 1f, 1f, 1f);
        return (int) curX;
    }
    private float drawRun(String run, float x, float y, int color) {
        if (run.isEmpty()) return x;
        GlyphTex tex = cache.get(run);
        if (tex == null) { tex = bake(run); cache.put(run, tex); }
        GlStateManager.bindTexture(tex.id);
        float r = (color >> 16 & 255) / 255f;
        float g = (color >> 8 & 255) / 255f;
        float b = (color & 255) / 255f;
        float a = (color >>> 24) / 255f;
        GlStateManager.color(r, g, b, a);
        float s = tex.scale;
        GlStateManager.pushMatrix();
        GlStateManager.scale(s, s, 1f);
        float dx = x / s;
        float dy = y / s;
        float dw = tex.width;
        float dh = tex.height;
        Tessellator t = Tessellator.getInstance();
        WorldRenderer wr = t.getWorldRenderer();
        wr.begin(7, DefaultVertexFormats.POSITION_TEX);
        wr.pos(dx, dy + dh, 0.0D).tex(0.0D, 1.0D).endVertex();
        wr.pos(dx + dw, dy + dh, 0.0D).tex(1.0D, 1.0D).endVertex();
        wr.pos(dx + dw, dy, 0.0D).tex(1.0D, 0.0D).endVertex();
        wr.pos(dx, dy, 0.0D).tex(0.0D, 0.0D).endVertex();
        t.draw();
        GlStateManager.popMatrix();
        return x + tex.width * s;
    }
    @Override
    public int getStringWidth(String text) {
        if (text == null || text.isEmpty()) return 0;
        float w = 0;
        int i = 0;
        final int n = text.length();
        StringBuilder run = new StringBuilder();
        while (i < n) {
            if (text.charAt(i) == '\\u00a7' && i + 1 < n) { if (run.length() > 0) { w += runWidth(run.toString()); run.setLength(0); } i += 2; continue; }
            run.append(text.charAt(i)); i++;
        }
        if (run.length() > 0) w += runWidth(run.toString());
        return (int) Math.ceil(w);
    }
    private float runWidth(String run) { if (run.isEmpty()) return 0; GlyphTex tex = cache.get(run); if (tex == null) { tex = bake(run); cache.put(run, tex); } return tex.width * tex.scale; }
    @Override
    public int getCharWidth(char c) { if (c == '\\u00a7') return -1; return getStringWidth(String.valueOf(c)); }
    @Override
    public boolean getUnicodeFlag() { return false; }
    @Override
    public String trimStringToWidth(String text, int width) { return trimStringToWidth(text, width, false); }
    @Override
    public String trimStringToWidth(String text, int width, boolean reverse) {
        if (text == null || text.isEmpty()) return "";
        StringBuilder out = new StringBuilder();
        float w = 0;
        int i = reverse ? text.length() - 1 : 0;
        int step = reverse ? -1 : 1;
        while (i >= 0 && i < text.length()) {
            char c = text.charAt(i);
            if (c == '\\u00a7' && i + step >= 0 && i + step < text.length()) { out.append(c).append(text.charAt(i + step)); i += step * 2; continue; }
            float cw = getStringWidth(String.valueOf(c));
            if (w + cw > width) break;
            out.append(c); w += cw; i += step;
        }
        if (reverse) out.reverse();
        return out.toString();
    }
    @Override
    public java.util.List<String> listFormattedStringToWidth(String text, int width) {
        java.util.List<String> out = new java.util.ArrayList<String>();
        if (text == null || text.isEmpty()) return out;
        String[] lines = text.split("\\n", -1);
        for (String line : lines) out.addAll(wrapFormattedStringToWidth(line, width));
        return out;
    }
    private java.util.List<String> wrapFormattedStringToWidth(String s, int width) {
        java.util.List<String> out = new java.util.ArrayList<String>();
        if (s == null || s.isEmpty()) { out.add(""); return out; }
        StringBuilder line = new StringBuilder();
        float w = 0;
        int i = 0;
        while (i < s.length()) {
            char c = s.charAt(i);
            if (c == '\\u00a7' && i + 1 < s.length()) { line.append(c).append(s.charAt(i + 1)); i += 2; continue; }
            if (c == ' ') {
                float sw = getStringWidth(" ");
                if (w + sw > width) { out.add(line.toString()); line.setLength(0); w = 0; }
                else { line.append(c); w += sw; }
                i++; continue;
            }
            int j = i;
            while (j < s.length() && s.charAt(j) != ' ' && s.charAt(j) != '\\u00a7') j++;
            String word = s.substring(i, j);
            float ww = getStringWidth(word);
            if (w + ww > width && line.length() > 0) { out.add(line.toString()); line.setLength(0); w = 0; }
            line.append(word); w += ww; i = j;
        }
        if (line.length() > 0) out.add(line.toString());
        return out;
    }
    @Override
    public void onResourceManagerReload(net.minecraft.client.resources.IResourceManager rm) { }
}"""
}

# Files to delete (icons, complex backgrounds, etc.)
files_to_delete = [
    "src/main/java/com/oryvex/kbclient/ui/Draw.java.bak",
    "src/main/java/com/oryvex/kbclient/ui/GuiKbOptions.java.bak"
]

def apply_changes():
    print("Applying simpler design changes...")
    
    # Modify files
    for path, content in files_to_modify.items():
        full_path = os.path.join(".", path)
        if os.path.exists(full_path):
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {path}")
        else:
            print(f"Warning: File not found: {path}")

    # Delete files
    for path in files_to_delete:
        full_path = os.path.join(".", path)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"Deleted: {path}")

    # Note: Transparency fixes for Scoreboard/Tab/Chat usually require ASM or Coremod 
    # which is beyond simple file replacement in a standard Forge mod without API hooks.
    # However, we can ensure our custom UI elements don't interfere.
    # The 'ModernFontRenderer' update ensures better text handling.
    
    print("Changes applied successfully.")

if __name__ == "__main__":
    apply_changes()