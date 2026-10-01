#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fixer.py  —  KB Client 3.0 full GUI / font / colour / responsive fix
Run from the project root (the folder that contains `src/`).
"""
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# locate project root (folder that contains src/main/java)
# ---------------------------------------------------------------------------
def find_root() -> Path:
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        if (p / "src" / "main" / "java").is_dir():
            return p
    # fallback: cwd
    if (Path.cwd() / "src" / "main" / "java").is_dir():
        return Path.cwd()
    sys.exit("Could not find project root (missing src/main/java).")

ROOT = find_root()
JAVA = ROOT / "src" / "main" / "java" / "com" / "oryvex" / "kbclient"
UI   = JAVA / "ui"
FONT = JAVA / "font"
RES  = ROOT / "src" / "main" / "resources"

UI.mkdir(parents=True, exist_ok=True)
FONT.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)
(RES / "fonts").mkdir(parents=True, exist_ok=True)


def write(path: Path, content: str, header: str = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if header:
        content = header + "\n" + content
    path.write_text(content, encoding="utf-8")
    print(f"  [WRITE] {path.relative_to(ROOT)}")


def patch(path: Path, old: str, new: str, required=True):
    if not path.exists():
        if required:
            print(f"  [SKIP ] {path.relative_to(ROOT)} (not found)")
        return False
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        if required:
            print(f"  [WARN ] pattern not found in {path.relative_to(ROOT)}")
        return False
    path.write_text(txt.replace(old, new, 1), encoding="utf-8")
    print(f"  [PATCH] {path.relative_to(ROOT)}")
    return True


# ===========================================================================
# 1. Theme.java — fix the scale constants (they were pixel sizes, needed
#    multipliers).  This is the root cause of the giant overlapping text.
# ===========================================================================
THEME = r'''package com.oryvex.kbclient.ui;

/** Colour palette + selectable accent themes (Settings.theme). */
public final class Theme {
    private Theme() {}

    // ---- surfaces ---------------------------------------------------------
    public static final int BG0 = 0xFF05060B;
    public static final int BG1 = 0xFF0B0D16;
    public static final int SURFACE = 0xEB0D0F17;   // window / big card
    public static final int SURFACE2 = 0xFF141722;  // raised card
    public static final int SURFACE3 = 0xFF1C2030;  // hover / pressed
    public static final int GLASS = 0xA6090B12;     // translucent panel
    public static final int FILL = 0x16FFFFFF;      // subtle light fill (buttons)
    public static final int FILL_HI = 0x2AFFFFFF;   // hovered light fill
    public static final int STROKE = 0x1FFFFFFF;
    public static final int STROKE_HI = 0x47FFFFFF;

    // ---- status ------------------------------------------------------------
    public static final int GOOD = 0xFF34D399;
    public static final int WARN = 0xFFFBBF24;
    public static final int BAD = 0xFFFB7185;

    // ---- text --------------------------------------------------------------
    public static final int TEXT = 0xFFF4F6FB;
    public static final int SOFT = 0xFFB4BCCF;
    public static final int MUTED = 0xFF7C86A2;
    public static final int DIM = 0xFF4A5169;

    // ---- type scale (MULTIPLIERS on the vanilla 9px font) ------------------
    // These were pixel sizes before (7f / 8f / 9f / 11f / 14f) which made
    // Draw.mid() render text at 9x scale.  Keep them as scale multipliers.
    public static final float T_XS = 0.75f;
    public static final float T_SM = 0.85f;
    public static final float T_MD = 1.00f;
    public static final float T_LG = 1.25f;
    public static final float T_XL = 1.60f;

    /** Minecraft colour-code prefix (chat only). */
    public static final String S = "\u00a7";

    // ---- accent themes -----------------------------------------------------
    public static final String[] THEME_NAMES = { "Ocean", "Violet", "Sunset", "Mint", "Rose", "Mono" };
    private static final int[][] PAL = {
        { 0xFF38BDF8, 0xFF6366F1 },
        { 0xFFA78BFA, 0xFFEC4899 },
        { 0xFFFB923C, 0xFFF43F5E },
        { 0xFF34D399, 0xFF22D3EE },
        { 0xFFF472B6, 0xFFFB7185 },
        { 0xFFE5E7EB, 0xFF94A3B8 }
    };

    private static int idx() {
        int t = Settings.theme;
        return t < 0 ? 0 : (t >= PAL.length ? PAL.length - 1 : t);
    }

    public static int accent() { return PAL[idx()][0]; }
    public static int accent2() { return PAL[idx()][1]; }
    public static int accentMid() { return Draw.lerp(accent(), accent2(), 0.5f); }

    /** accent -> accent2 -> accent ping-pong that slowly flows over time. */
    public static int flow(float offset) {
        float p = ((System.currentTimeMillis() % 7000L) / 7000f + offset) % 1f;
        if (p < 0f) p += 1f;
        float tri = p < 0.5f ? p * 2f : (1f - p) * 2f;
        return Draw.lerp(accent(), accent2(), tri);
    }

    public static float phase() { return (System.currentTimeMillis() % 7000L) / 7000f; }

    // ---- legacy aliases (used by older screens) ----------------------------
    public static final int PANEL = 0xFF121A29;
    public static final int PANEL2 = 0xFF182235;
    public static final int PANEL3 = 0xFF22304A;
    public static final int BORDER = 0xFF25324B;
    public static final int BORDER_HI = 0xFF3B5078;
    public static final int ACCENT = 0xFF22D3EE;
    public static final int ACCENT_DK = 0xFF0E7490;
    public static final int ACCENT2 = 0xFFA78BFA;
}
'''
write(UI / "Theme.java", THEME)


# ===========================================================================
# 2. ModernFontRenderer.java — proper Persian/Arabic shaping with TextLayout,
#    and correct per-string scale so measuring and drawing match exactly.
# ===========================================================================
FONT_JAVA = r'''package com.oryvex.kbclient.font;

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
'''
write(FONT / "ModernFontRenderer.java", FONT_JAVA)


# ===========================================================================
# 3. Settings.java — full version with every field used by the new UI.
# ===========================================================================
SETTINGS = r'''package com.oryvex.kbclient.ui;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.Properties;
import net.minecraft.client.Minecraft;

public final class Settings {
    private Settings() {}

    public static final String[] FADE_NAMES = { "Off", "Fast", "Normal", "Slow" };

    public static boolean hud = true;
    public static boolean watermark = true;
    public static boolean particles = true;
    public static boolean aurora = true;
    public static boolean toasts = true;
    public static boolean customLoading = true;
    public static boolean discordRpc = true;
    public static int fade = 2;
    public static int theme = 0;
    /** particle density 0..100 */
    public static int density = 60;

    public static File dir() {
        File d = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!d.exists()) d.mkdirs();
        return d;
    }

    private static File file() { return new File(dir(), "settings.properties"); }

    private static int num(Properties p, String k, int def, int lo, int hi) {
        try {
            int v = Integer.parseInt(p.getProperty(k, String.valueOf(def)).trim());
            return Math.max(lo, Math.min(hi, v));
        } catch (Throwable t) { return def; }
    }

    private static boolean flag(Properties p, String k, boolean def) {
        return Boolean.parseBoolean(p.getProperty(k, String.valueOf(def)).trim());
    }

    public static void resetDefaults() {
        hud = true; watermark = true; particles = true; aurora = true; toasts = true;
        customLoading = true; discordRpc = true; fade = 2; theme = 0; density = 60;
    }

    public static void load() {
        try {
            File f = file();
            if (!f.exists()) return;
            Properties p = new Properties();
            FileInputStream in = new FileInputStream(f);
            try { p.load(in); } finally { in.close(); }
            hud = flag(p, "hud", true);
            watermark = flag(p, "watermark", true);
            particles = flag(p, "particles", true);
            aurora = flag(p, "aurora", true);
            toasts = flag(p, "toasts", true);
            customLoading = flag(p, "customLoading", true);
            discordRpc = flag(p, "discordRpc", true);
            fade = num(p, "fade", 2, 0, 3);
            theme = num(p, "theme", 0, 0, Theme.THEME_NAMES.length - 1);
            density = num(p, "density", 60, 0, 100);
        } catch (Throwable ignored) { }
    }

    public static void save() {
        try {
            Properties p = new Properties();
            p.setProperty("hud", String.valueOf(hud));
            p.setProperty("watermark", String.valueOf(watermark));
            p.setProperty("particles", String.valueOf(particles));
            p.setProperty("aurora", String.valueOf(aurora));
            p.setProperty("toasts", String.valueOf(toasts));
            p.setProperty("customLoading", String.valueOf(customLoading));
            p.setProperty("discordRpc", String.valueOf(discordRpc));
            p.setProperty("fade", String.valueOf(fade));
            p.setProperty("theme", String.valueOf(theme));
            p.setProperty("density", String.valueOf(density));
            FileOutputStream out = new FileOutputStream(file());
            try { p.store(out, "KB Client settings"); } finally { out.close(); }
        } catch (Throwable ignored) { }
    }
}
'''
write(UI / "Settings.java", SETTINGS)


# ===========================================================================
# 4. Draw.java — remove the heavy GL_LINE_LOOP glow from panel() (it was
#    expensive and could break on some drivers), replace it with a light
#    rounded shadow, and normalise the text API so pixel sizes never again
#    get interpreted as multipliers.
# ===========================================================================
DRAW = UI / "Draw.java"
if DRAW.exists():
    txt = DRAW.read_text(encoding="utf-8")

    # --- replace panel() ---------------------------------------------------
    old_panel_re = re.compile(
        r"public static void panel\(float x, float y, float w, float h, float r, int fill, int border\) \{.*?\n    \}",
        re.S,
    )
    new_panel = (
        "public static void panel(float x, float y, float w, float h, float r, int fill, int border) {\n"
        "        if (((fill >>> 24) & 255) > 4) {\n"
        "            // Soft drop shadow (cheap, safe, works on all drivers).\n"
        "            roundRect(x + 1f, y + 2f, w, h, r, 0x44000000);\n"
        "            roundRect(x, y, w, h, r, fill);\n"
        "        }\n"
        "        if (border != 0 && ((border >>> 24) & 255) > 4) {\n"
        "            roundOutline(x, y, w, h, r, 1f, border);\n"
        "        }\n"
        "    }"
    )
    txt2, n = old_panel_re.subn(new_panel, txt, count=1)
    if n:
        print("  [PATCH] Draw.panel()")
        txt = txt2
    else:
        print("  [WARN ] Draw.panel() pattern not matched")

    # --- replace text()/mid()/left()/right() so scale is always a multiplier --
    # Draw.text already took a multiplier — good.  Only mid()/left()/right() are
    # called with Theme.T_* values which are now multipliers, so no change needed.
    DRAW.write_text(txt, encoding="utf-8")


# ===========================================================================
# 5. GuiModernMenu.java — responsive layout, safe for tiny windows.
# ===========================================================================
MENU = r'''package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBClientMod;
import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiMultiplayer;
import net.minecraft.client.gui.GuiSelectWorld;

public class GuiModernMenu extends FadeScreen {
    private final KBTracker tracker;
    private int sidebarW;

    public GuiModernMenu(KBTracker tracker) {
        this.tracker = tracker;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();

        // Responsive sidebar: 26% of width, clamped.
        sidebarW = Math.max(180, Math.min(300, (int) (this.width * 0.26f)));

        int padding = Math.max(12, sidebarW / 10);
        int bw = sidebarW - padding * 2;
        int bh = Math.max(20, Math.min(28, this.height / 22));
        int gap = Math.max(4, bh / 5);

        int totalHeight = 6 * bh + 5 * gap;
        int top = Math.max(72, (this.height - totalHeight) / 2 + 10);

        this.buttonList.add(new UiButton(1, padding, top, bw, bh, "Singleplayer").delay(100));
        this.buttonList.add(new UiButton(2, padding, top + (bh + gap), bw, bh, "Multiplayer").delay(150));
        this.buttonList.add(new UiButton(6, padding, top + 2 * (bh + gap), bw, bh, "Alt Manager").delay(200));
        this.buttonList.add(new UiButton(3, padding, top + 3 * (bh + gap), bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(250));
        this.buttonList.add(new UiButton(4, padding, top + 4 * (bh + gap), bw, bh, "Options").icon(UiButton.ICON_GEAR).delay(300));
        this.buttonList.add(new UiButton(5, padding, top + 5 * (bh + gap), bw, bh, "Quit").style(UiButton.DANGER).delay(350));
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: closeTo(new GuiSelectWorld(this)); break;
            case 2: closeTo(new GuiMultiplayer(this)); break;
            case 3: closeTo(new GuiAnalyzer(tracker, this)); break;
            case 4: closeTo(new GuiKbOptions(tracker, this)); break;
            case 6: closeTo(new GuiAltManager(this)); break;
            case 5:
                closeThen(new Runnable() {
                    @Override public void run() { mc.shutdown(); }
                });
                break;
            default: break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        // main menu cannot be closed with ESC
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        // Background
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);

        // Sidebar panel
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // -------- Title -------------------------------------------------
        String title = "ORYVEX";
        float titleScale = Math.max(1.4f, Math.min(2.2f, sidebarW / 130f));
        float titleW = Draw.font().getStringWidth(title) * titleScale;
        float titleY = Math.max(24f, this.height * 0.09f);
        Draw.text(title, (sidebarW - titleW) / 2f, titleY, Theme.TEXT, titleScale, true);

        String sub = "KB Client v" + KBClientMod.VERSION;
        float subScale = 0.85f;
        float subW = Draw.font().getStringWidth(sub) * subScale;
        Draw.text(sub, (sidebarW - subW) / 2f, titleY + 26, Theme.ACCENT, subScale, false);

        Draw.rect(20, titleY + 44, sidebarW - 40, 1, Theme.BORDER);

        // -------- Profile widget (top-right) ----------------------------
        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Profile:  " + p.summary();
            int w = Draw.width(s, 0.85f) + 34;
            int px = this.width - w - 14;
            int py = 14;
            if (px > sidebarW + 8) {
                Draw.roundRect(px, py, w, 22, 6f, Theme.PANEL2);
                Draw.roundOutline(px, py, w, 22, 6f, 1f, Theme.BORDER);
                Draw.roundRect(px + 9, py + 8, 6, 6, 3f, Theme.GOOD);
                Draw.text(s, px + 22, py + 7, Theme.TEXT, 0.85f, false);
            }
        }

        // -------- User card (bottom) -----------------------------------
        int userY = this.height - Math.max(34, 40);
        Draw.rect(20, userY - 12, sidebarW - 40, 1, Theme.BORDER);

        Draw.roundRect(20, userY - 2, 20, 20, 10f, Theme.PANEL3);
        Draw.centered("L", 30, userY + 4, Theme.SOFT, 1.0f, false);

        Draw.text("Logged in as", 46, userY, Theme.MUTED, 0.75f, false);
        String name = mc.getSession().getUsername();
        int nameMax = sidebarW - 56;
        String nameF = Draw.fit(name, nameMax, 0.95f, false);
        Draw.text(nameF, 46, userY + 10, Theme.TEXT, 0.95f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
'''
write(UI / "GuiModernMenu.java", MENU)


# ===========================================================================
# 6. UI-BUTTON — make sure the new Theme multiplier is applied consistently.
#    UiButton uses `textSize = Theme.T_MD` (now 1.0f).  No further patch needed.
# ===========================================================================


# ===========================================================================
# 7. Make sure the mod actually registers the custom font on startup.
#    Patch KBClientMod.init if it doesn't already do this.
# ===========================================================================
MOD = JAVA / "KBClientMod.java"
if MOD.exists():
    txt = MOD.read_text(encoding="utf-8")
    if "ModernFontRenderer" not in txt:
        anchor = "DiscordRPC.start();"
        if anchor in txt:
            inject = (
                anchor + "\n\n"
                "          try {\n"
                "              net.minecraft.client.Minecraft mc = net.minecraft.client.Minecraft.getMinecraft();\n"
                "              mc.fontRendererObj = new com.oryvex.kbclient.font.ModernFontRenderer(\n"
                "                      mc.gameSettings,\n"
                "                      new net.minecraft.util.ResourceLocation(\"textures/font/ascii.png\"),\n"
                "                      mc.renderEngine, false);\n"
                "              logger.info(\"[KBClient] ModernFontRenderer attached\");\n"
                "          } catch (Throwable t) {\n"
                "              logger.error(\"[KBClient] ModernFontRenderer failed: \" + t);\n"
                "          }"
            )
            txt = txt.replace(anchor, inject, 1)
            MOD.write_text(txt, encoding="utf-8")
            print("  [PATCH] KBClientMod.init -> ModernFontRenderer wired in")
        else:
            print("  [WARN ] could not find DiscordRPC.start() anchor in KBClientMod")
    else:
        print("  [SKIP ] KBClientMod already registers ModernFontRenderer")


# ===========================================================================
# 8. Small sanity fix on GuiAltManager — the title / card math used the old
#    Theme constants, so nothing to change once Theme is fixed.
# ===========================================================================


# ===========================================================================
# 9. Font files — check they exist, warn if not.
# ===========================================================================
for name in ("Inter-Regular.ttf", "Vazirmatn-Regular.ttf"):
    fp = RES / "fonts" / name
    if fp.exists():
        print(f"  [ OK  ] fonts/{name}")
    else:
        print(f"  [WARN ] fonts/{name} missing — CI will download it (see .github/workflows/build.yml)")


print("\nAll done.  Rebuild with:  ./gradlew clean build")
print("If text still looks too big, delete .minecraft/kbclient/settings.properties")
print("and restart so the new Theme defaults apply.")