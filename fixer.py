#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fixer_v3.py — چت با فونت فارسی/انگلیسی + آیکون درست + دکمه‌های جدید
از ریشه پروژه اجرا کن.
"""
import sys
from pathlib import Path


def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "src" / "main" / "java").is_dir():
            return p
    if (Path.cwd() / "src" / "main" / "java").is_dir():
        return Path.cwd()
    sys.exit("Project root not found.")


ROOT = find_root()
JAVA = ROOT / "src" / "main" / "java" / "com" / "oryvex" / "kbclient"
UI   = JAVA / "ui"
FONT = JAVA / "font"

for d in (UI, FONT):
    d.mkdir(parents=True, exist_ok=True)


def write(path: Path, body: str):
    path.write_text(body, encoding="utf-8")
    print(f"  [WRITE] {path.relative_to(ROOT)}")


# ===========================================================================
# 1) ModernFontRenderer — حالا برای **چت هم** استفاده می‌شه
#    - BiDi درست با TextLayout (کلمه‌به‌کلمه نه حرف‌به‌حرف)
#    - trimStringToWidth / listFormattedStringToWidth کامل
#    - getStringWidth دقیق
# ===========================================================================
write(FONT / "ModernFontRenderer.java", r'''package com.oryvex.kbclient.font;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.font.FontRenderContext;
import java.awt.font.TextAttribute;
import java.awt.font.TextLayout;
import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.text.AttributedString;
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

/**
 * AWT-backed font renderer with proper Arabic/Persian shaping and RTL support.
 * Used for both the custom UI and the vanilla chat by replacing mc.fontRendererObj.
 *
 * The renderer draws the whole string through a single TextLayout so bidi
 * reordering is correct. Colour formatting codes (\u00a7x) are handled by
 * splitting the string into coloured runs before shaping.
 */
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

    private final Map<String, GlyphTex> cache = new LinkedHashMap<String, GlyphTex>(1024, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, GlyphTex> eldest) {
            if (size() > 1024) {
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

    /** Mixed script: from position 0, is the visual order RTL? */
    public static boolean isRtlDominant(String text) {
        int rtl = 0, ltr = 0;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c >= 0x0590 && c <= 0x08FF) rtl++;
            else if (Character.isLetter(c)) ltr++;
        }
        return rtl > ltr;
    }

    /** Bake whole string via TextLayout. Bidi handled internally. */
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

        // Split by § codes into (substring, color) runs, keeping bidi correctness
        // inside each run. Since § only appears at run boundaries, each run is
        // shaped independently by TextLayout — this is exactly what we want.
        float curX = x;
        int curColor = color;
        if ((curColor & 0xFC000000) == 0) curColor |= 0xFF000000;
        if (shadow) curColor = (curColor & 0xFCFCFC) >> 2 | (curColor & 0xFF000000);

        int i = 0;
        final int n = text.length();
        StringBuilder run = new StringBuilder();
        while (i < n) {
            if (text.charAt(i) == '\u00a7' && i + 1 < n) {
                // flush current run
                if (run.length() > 0) {
                    curX = drawRun(run.toString(), curX, y, curColor);
                    run.setLength(0);
                }
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
            run.append(text.charAt(i));
            i++;
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
        float g = (color >> 8  & 255) / 255f;
        float b = ( color       & 255) / 255f;
        float a = (color >>> 24      ) / 255f;
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
        wr.pos(dx,      dy + dh, 0.0D).tex(0.0D, 1.0D).endVertex();
        wr.pos(dx + dw, dy + dh, 0.0D).tex(1.0D, 1.0D).endVertex();
        wr.pos(dx + dw, dy,      0.0D).tex(1.0D, 0.0D).endVertex();
        wr.pos(dx,      dy,      0.0D).tex(0.0D, 0.0D).endVertex();
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
            if (text.charAt(i) == '\u00a7' && i + 1 < n) {
                if (run.length() > 0) {
                    w += runWidth(run.toString());
                    run.setLength(0);
                }
                i += 2;
                continue;
            }
            run.append(text.charAt(i));
            i++;
        }
        if (run.length() > 0) w += runWidth(run.toString());
        return (int) Math.ceil(w);
    }

    private float runWidth(String run) {
        if (run.isEmpty()) return 0;
        GlyphTex tex = cache.get(run);
        if (tex == null) { tex = bake(run); cache.put(run, tex); }
        return tex.width * tex.scale;
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
''')


# ===========================================================================
# 2) Draw.java — آیکون gear تمام‌برداری (بدون roundRect در اندازه کوچک)
#    و دکمه‌های جدید تمیز
# ===========================================================================
DRAW = UI / "Draw.java"
txt = DRAW.read_text(encoding="utf-8")

# جایگزینی gear() با یک چرخ‌دنده تمام‌برداری
old_gear_start = txt.find("    public static void gear(")
old_gear_end   = txt.find("    public static void icon(", old_gear_start)
new_gear = '''    /**
     * Pixel-perfect vector gear icon, drawn with GL lines + triangles.
     * Looks the same at any size — the old roundRect-based version broke
     * on small buttons (see issue with Options button).
     */
    public static void gear(float cx, float cy, float r, float angle, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        if (r < 1.5f) return;

        float or = r;          // outer radius (tooth tip)
        float ir = r * 0.62f;  // inner radius (body)
        float tr = r * 0.28f;  // tooth width
        int teeth = 8;

        float ar = (float) Math.toRadians(angle);

        GlStateManager.disableTexture2D();
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);

        float rr = ((color >> 16) & 255) / 255f;
        float gg = ((color >> 8)  & 255) / 255f;
        float bb = ( color        & 255) / 255f;
        float aa = ((color >>> 24)      ) / 255f;
        GlStateManager.color(rr, gg, bb, aa);

        // --- teeth as quads ---
        for (int i = 0; i < teeth; i++) {
            double a0 = ar + (2 * Math.PI * i) / teeth;
            double a1 = a0 + (2 * Math.PI / teeth) * 0.55;

            float x0 = cx + (float)Math.cos(a0) * ir;
            float y0 = cy + (float)Math.sin(a0) * ir;
            float x1 = cx + (float)Math.cos(a1) * ir;
            float y1 = cy + (float)Math.sin(a1) * ir;

            float dx = x1 - x0, dy = y1 - y0;
            float len = (float)Math.sqrt(dx * dx + dy * dy);
            if (len < 0.001f) continue;
            float nx = -dy / len * (tr * 0.5f);
            float ny =  dx / len * (tr * 0.5f);

            float tx0 = x0 + nx, ty0 = y0 + ny;
            float tx1 = x1 + nx, ty1 = y1 + ny;
            float tx2 = x1 - nx, ty2 = y1 - ny;
            float tx3 = x0 - nx, ty3 = y0 - ny;

            float ex0 = cx + (float)Math.cos(a0) * or;
            float ey0 = cy + (float)Math.sin(a0) * or;
            float ex1 = cx + (float)Math.cos(a1) * or;
            float ey1 = cy + (float)Math.sin(a1) * or;

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx0, ty0);
            org.lwjgl.opengl.GL11.glVertex2f(tx1, ty1);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx1, ty1);
            org.lwjgl.opengl.GL11.glVertex2f(tx2, ty2);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx2, ty2);
            org.lwjgl.opengl.GL11.glVertex2f(tx3, ty3);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();

            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_QUADS);
            org.lwjgl.opengl.GL11.glVertex2f(tx3, ty3);
            org.lwjgl.opengl.GL11.glVertex2f(tx0, ty0);
            org.lwjgl.opengl.GL11.glVertex2f(ex1, ey1);
            org.lwjgl.opengl.GL11.glVertex2f(ex0, ey0);
            org.lwjgl.opengl.GL11.glEnd();
        }

        // --- inner disc ---
        org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_TRIANGLE_FAN);
        org.lwjgl.opengl.GL11.glVertex2f(cx, cy);
        for (int i = 0; i <= 32; i++) {
            double a = ar + (2 * Math.PI * i) / 32;
            org.lwjgl.opengl.GL11.glVertex2f(
                cx + (float)Math.cos(a) * ir,
                cy + (float)Math.sin(a) * ir);
        }
        org.lwjgl.opengl.GL11.glEnd();

        // --- centre hole ---
        int bg = 0;
        try {
            bg = (org.lwjgl.opengl.GL11.glGetInteger(org.lwjgl.opengl.GL11.GL_BLEND) != 0) ? 0x00000000 : 0x00000000;
        } catch (Throwable ignored) {}
        org.lwjgl.opengl.GL11.glColor4f(0f, 0f, 0f, 0f);
        org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_TRIANGLE_FAN);
        org.lwjgl.opengl.GL11.glVertex2f(cx, cy);
        for (int i = 0; i <= 24; i++) {
            double a = (2 * Math.PI * i) / 24;
            org.lwjgl.opengl.GL11.glVertex2f(
                cx + (float)Math.cos(a) * (r * 0.24f),
                cy + (float)Math.sin(a) * (r * 0.24f));
        }
        org.lwjgl.opengl.GL11.glEnd();

        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.enableTexture2D();
    }

    /** Legacy signature (angle + hole). Kept so old callers keep compiling. */
    public static void gear(float cx, float cy, float r, float angle, int color, int hole) {
        gear(cx, cy, r, angle, color);
    }

'''
txt = txt[:old_gear_start] + new_gear + txt[old_gear_end:]

# جایگزینی icon() با یک نسخه‌ی بهتر (بدون بلاک تکراری)
old_icon_start = txt.find("    public static void icon(")
old_icon_end   = txt.find("    /** فونت UI ما:", old_icon_start)
if old_icon_end == -1:
    old_icon_end = txt.find("    public static FontRenderer font()", old_icon_start)
new_icon = '''    public static void icon(int type, float cx, float cy, float size, int color) {
        float h = size / 2f;
        if (type == ICON_ARROW) {
            GlStateManager.disableTexture2D();
            GlStateManager.enableBlend();
            float rr = ((color >> 16) & 255) / 255f;
            float gg = ((color >> 8)  & 255) / 255f;
            float bb = ( color        & 255) / 255f;
            float aa = ((color >>> 24)      ) / 255f;
            GlStateManager.color(rr, gg, bb, aa);
            org.lwjgl.opengl.GL11.glBegin(org.lwjgl.opengl.GL11.GL_TRIANGLES);
            org.lwjgl.opengl.GL11.glVertex2f(cx - h * 0.6f, cy - h);
            org.lwjgl.opengl.GL11.glVertex2f(cx - h * 0.6f, cy + h);
            org.lwjgl.opengl.GL11.glVertex2f(cx + h * 0.9f, cy);
            org.lwjgl.opengl.GL11.glEnd();
            GlStateManager.color(1f, 1f, 1f, 1f);
            GlStateManager.enableTexture2D();
        } else if (type == ICON_GEAR) {
            gear(cx, cy, h, 0, color);
        } else {
            rect(cx - h, cy - h, size, size, color);
        }
    }

'''
txt = txt[:old_icon_start] + new_icon + txt[old_icon_end:]

DRAW.write_text(txt, encoding="utf-8")
print(f"  [PATCH] {DRAW.relative_to(ROOT)}  (new gear + icon)")


# ===========================================================================
# 3) UiButton.java — استفاده از امضاى جديد gear() + طراحى بهتر
# ===========================================================================
BUTTON = UI / "UiButton.java"
txt = BUTTON.read_text(encoding="utf-8")

# پیدا کردن فراخوانی gear با hole argument
txt = txt.replace(
    "if (icon == ICON_GEAR) Draw.gear(ix, cy, isz * 1.15f, spin, ic, 0);",
    "if (icon == ICON_GEAR) Draw.gear(ix, cy, isz * 1.15f, spin, ic);"
)
BUTTON.write_text(txt, encoding="utf-8")
print(f"  [PATCH] {BUTTON.relative_to(ROOT)}")


# ===========================================================================
# 4) KBClientMod — override mc.fontRendererObj با ModernFontRenderer
#    (اینجا **هم** چت از فونت فارسى پشتیبانى مى‌کنه)
# ===========================================================================
MOD = JAVA / "KBClientMod.java"
txt = MOD.read_text(encoding="utf-8")

# حذف بلوک قدیمى که فقط modernFont رو مى‌ساخت
import re
txt = re.sub(
    r"\n\s*try\s*\{\s*\n\s*Minecraft mcFont = Minecraft\.getMinecraft\(\);\s*\n\s*modernFont = new com\.oryvex\.kbclient\.font\.ModernFontRenderer.*?\n\s*\}\s*catch \(Throwable t\) \{\s*\n\s*logger\.error\(\"\[KBClient\] ModernFontRenderer failed.*?\n\s*\}",
    "", txt, flags=re.S,
)

# اضافه کردن بلوک جدید در init
anchor = "installLoading();"
if anchor in txt and "ModernFontRenderer attached to mc.fontRendererObj" not in txt:
    inject = (
        anchor + "\n"
        "          try {\n"
        "              Minecraft mcF = Minecraft.getMinecraft();\n"
        "              modernFont = new com.oryvex.kbclient.font.ModernFontRenderer(\n"
        "                      mcF.gameSettings,\n"
        "                      new net.minecraft.util.ResourceLocation(\"textures/font/ascii.png\"),\n"
        "                      mcF.renderEngine, false);\n"
        "              mcF.fontRendererObj = modernFont;\n"
        "              logger.info(\"[KBClient] ModernFontRenderer attached to mc.fontRendererObj\");\n"
        "          } catch (Throwable t) {\n"
        "              logger.error(\"[KBClient] ModernFontRenderer failed: \" + t);\n"
        "          }"
    )
    txt = txt.replace(anchor, inject, 1)

MOD.write_text(txt, encoding="utf-8")
print(f"  [PATCH] {MOD.relative_to(ROOT)}  (mc.fontRendererObj overridden)")


print()
print("Done.  Rebuild:  .\\gradlew clean build")
print("اگر چت هنوز فارسى رو درست نشون نمى‌ده، در تنظیمات گرافیکى Minecraft گزینه Force Unicode Font رو روشن کن.")