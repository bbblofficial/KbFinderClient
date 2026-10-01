import os

def apply_premium_client_ui():
    print("🚀 Upgrading to Ultimate Rise / LiquidBounce Style UI...")

    # 1. Premium Theme (Vivid, Deep, Modern)
    theme_code = """package com.oryvex.kbclient.ui;

public final class Theme {
    private Theme() {}

    public static final int BG0 = 0xFF05050A; // Extremely dark void
    public static final int BG1 = 0xFF0D0E15; 
    public static final int PANEL = 0x8505060A; // Deep Glass
    public static final int PANEL2 = 0x55FFFFFF;
    public static final int PANEL3 = 0x33FFFFFF;
    public static final int BORDER = 0x1AFFFFFF; // Super subtle edge
    public static final int BORDER_HI = 0x44FFFFFF;
    public static final int GLASS = 0x77000000;

    public static final int ACCENT = 0xFF3B82F6; // Modern Blue
    public static final int ACCENT_DK = 0xFF2563EB;
    public static final int ACCENT2 = 0xFF8B5CF6; // Modern Purple

    public static final int GOOD = 0xFF10B981;
    public static final int WARN = 0xFFF59E0B;
    public static final int BAD = 0xFFF43F5E;

    public static final int TEXT = 0xFFFFFFFF;
    public static final int SOFT = 0xFF94A3B8;
    public static final int MUTED = 0xFF475569;
    public static final int DIM = 0xFF1E293B;

    public static final String S = "\u00a7";
}
"""

    # 2. Advanced Draw with Plexus Background
    draw_code = """package com.oryvex.kbclient.ui;

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
"""

    # 3. Premium Sidebar Minimalist Buttons
    button_code = """package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.renderer.GlStateManager;

public class UiButton extends GuiButton {
    public static final int NORMAL = 0, PRIMARY = 1, DANGER = 2, TAB = 3, TOGGLE = 4;
    public static final int ICON_NONE = 0, ICON_GEAR = 1;

    public int style = NORMAL;
    public int icon = ICON_NONE;
    public boolean selected;
    public boolean on;
    public long delay;

    private float hover, knob, spin;
    private final long born = System.currentTimeMillis();
    private long last = System.nanoTime();

    public UiButton(int id, int x, int y, int w, int h, String text) {
        super(id, x, y, w, h, text);
    }

    public UiButton style(int s) { this.style = s; return this; }
    public UiButton icon(int i) { this.icon = i; return this; }
    public UiButton delay(long d) { this.delay = d; return this; }

    @Override
    public void drawButton(Minecraft mc, int mouseX, int mouseY) {
        if (!this.visible) return;
        this.hovered = mouseX >= this.xPosition && mouseY >= this.yPosition && mouseX < this.xPosition + this.width && mouseY < this.yPosition + this.height;

        long nowN = System.nanoTime();
        float dt = Math.min(0.1f, (nowN - last) / 1.0e9f);
        last = nowN;
        hover += (((this.hovered && this.enabled) ? 1f : 0f) - hover) * Math.min(1f, dt * 18f);
        knob += ((on ? 1f : 0f) - knob) * Math.min(1f, dt * 20f);
        spin = (spin + dt * (40f + 380f * hover)) % 360f;

        float ap = Fade.ease((System.currentTimeMillis() - born - delay) / 320f);
        if (ap <= 0.01f) return;

        int fill, text;
        switch (style) {
            case PRIMARY:
                fill = Draw.lerp(0x00000000, Theme.ACCENT, hover);
                text = Draw.lerp(Theme.SOFT, Theme.TEXT, hover);
                break;
            case DANGER:
                fill = Draw.lerp(0x00000000, Theme.BAD, hover);
                text = Draw.lerp(Theme.SOFT, Theme.TEXT, hover);
                break;
            case TAB:
                fill = selected ? Theme.PANEL2 : Draw.lerp(0x00000000, Theme.PANEL, hover);
                text = selected ? Theme.ACCENT : Draw.lerp(Theme.MUTED, Theme.TEXT, hover);
                break;
            default:
                fill = Draw.lerp(0x00000000, Theme.PANEL3, hover);
                text = Draw.lerp(Theme.SOFT, Theme.TEXT, hover);
        }
        if (!enabled) { fill = 0x00000000; text = Theme.DIM; }

        Draw.blend();
        int y = yPosition + (int) ((1f - ap) * 8f);
        
        // Premium Sidebar Hover Effect (Fill fades in, left indicator line slides up)
        if (style != TAB && style != TOGGLE) {
            Draw.roundRect(xPosition, y, width, height, 4f, Draw.fade(fill, ap * 0.4f));
            if (hover > 0.01f) {
                float lineH = height * hover * 0.6f;
                int lineColor = style == PRIMARY ? Theme.ACCENT : (style == DANGER ? Theme.BAD : Theme.SOFT);
                Draw.roundRect(xPosition, y + (height - lineH)/2f, 2f, lineH, 1f, Draw.fade(lineColor, ap * hover));
                Draw.shadow(xPosition, y + (height - lineH)/2f, 2f, lineH, 1f, Draw.fade(lineColor, ap * hover), 4f);
            }
        } else {
            Draw.roundRect(xPosition, y, width, height, 4f, Draw.fade(fill, ap));
        }

        int tc = Draw.fade(text, ap);
        if (style == TOGGLE) {
            Draw.text(displayString, xPosition + 8, y + (height - 8) / 2f, tc, 1f, false);
            int sw = 22, sh = 10, sx = xPosition + width - 8 - sw, sy = y + (height - sh) / 2;
            Draw.roundRect(sx, sy, sw, sh, 5f, Draw.fade(Draw.lerp(Theme.PANEL3, Theme.ACCENT_DK, knob), ap));
            Draw.roundRect(sx + 1 + (sw - sh) * knob, sy + 1, sh - 2, sh - 2, 4f, Draw.fade(Theme.TEXT, ap));
            if(knob > 0.1f) Draw.shadow(sx + 1 + (sw - sh) * knob, sy + 1, sh - 2, sh - 2, 4f, Draw.fade(Theme.ACCENT, ap * knob), 4f);
        } else if (icon == ICON_GEAR) {
            int tw = Draw.width(displayString, 1f);
            float startX = xPosition + (width - (tw + 18)) / 2f;
            Draw.gear(startX + 6f, y + height / 2f, 4.5f, spin, Draw.fade(Draw.lerp(Theme.MUTED, Theme.ACCENT, hover), ap), Draw.fade(fill, ap));
            Draw.text(displayString, startX + 18f, y + (height - 8) / 2f, tc, 1f, true);
        } else {
            // Text pushes slightly to the right on hover
            float push = hover * 4f;
            Draw.text(displayString, xPosition + 12f + push, y + (height - 8) / 2f, tc, 1f, false);
        }
    }
}
"""

    # 4. GuiModernMenu (Glass Sidebar layout)
    modern_menu_code = """package com.oryvex.kbclient.ui;

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
        sidebarW = 200;
        int bw = 160, bh = 24, gap = 8;
        int bx = 20; 
        int top = this.height / 2 - (6 * bh + 5 * gap) / 2 + 10;

        this.buttonList.add(new UiButton(1, bx, top, bw, bh, "Singleplayer").delay(100));
        this.buttonList.add(new UiButton(2, bx, top + (bh + gap), bw, bh, "Multiplayer").delay(150));
        this.buttonList.add(new UiButton(6, bx, top + 2 * (bh + gap), bw, bh, "Alt Manager").delay(200));
        this.buttonList.add(new UiButton(3, bx, top + 3 * (bh + gap), bw, bh, "Analyzer").style(UiButton.PRIMARY).delay(250));
        this.buttonList.add(new UiButton(4, bx, top + 4 * (bh + gap), bw, bh, "Options").icon(UiButton.ICON_GEAR).delay(300));
        this.buttonList.add(new UiButton(5, bx, top + 5 * (bh + gap), bw, bh, "Quit").style(UiButton.DANGER).delay(350));
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
                    @Override
                    public void run() { mc.shutdown(); }
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
        // Dark animated gradient background
        Draw.vgradient(this.width, this.height, Theme.BG0, Theme.BG1);
        
        // Premium Plexus Effect
        if (Settings.particles) {
            Draw.plexusBackground(this.width, this.height, 0.45f);
        }

        // Glass Sidebar
        Draw.shadow(0, 0, sidebarW, this.height, 0f, 0xFF000000, 20f);
        Draw.rect(0, 0, sidebarW, this.height, Theme.PANEL);
        Draw.rect(sidebarW, 0, 1, this.height, Theme.BORDER);

        // Logo on sidebar
        Draw.text("K B   C L I E N T", 20, 35, Theme.TEXT, 1.4f, true);
        Draw.text("v" + KBClientMod.VERSION, 22, 52, Theme.ACCENT, 0.85f, false);
        Draw.rect(20, 70, sidebarW - 40, 1, Theme.BORDER);

        // Info Panel on the right (Rise Style Status)
        KBProfile p = tracker.getProfile();
        if (p.hasData) {
            String s = "Last Profile: " + p.summary() + " (" + p.used + " hits)";
            int w = Draw.width(s, 0.85f) + 24;
            int px = this.width - w - 20;
            int py = 20;
            Draw.shadow(px, py, w, 20, 6f, 0xFF000000, 8f);
            Draw.roundRect(px, py, w, 20, 6f, Theme.PANEL);
            Draw.roundRect(px, py, w, 20, 6f, Theme.BORDER);
            Draw.text(s, px + 12, py + 6.5f, Theme.SOFT, 0.85f, false);
            Draw.roundRect(px - 4, py + 6, 8, 8, 4f, Theme.GOOD); // Online dot
        }

        // Account Display Bottom Left
        String acc = "User: " + mc.getSession().getUsername();
        Draw.text(acc, 20, this.height - 20, Theme.MUTED, 0.85f, false);

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
"""

    # 5. Write files
    os.makedirs("src/main/java/com/oryvex/kbclient/ui", exist_ok=True)
    with open("src/main/java/com/oryvex/kbclient/ui/Theme.java", "w", encoding="utf-8") as f:
        f.write(theme_code)
    with open("src/main/java/com/oryvex/kbclient/ui/Draw.java", "w", encoding="utf-8") as f:
        f.write(draw_code)
    with open("src/main/java/com/oryvex/kbclient/ui/UiButton.java", "w", encoding="utf-8") as f:
        f.write(button_code)
    with open("src/main/java/com/oryvex/kbclient/ui/GuiModernMenu.java", "w", encoding="utf-8") as f:
        f.write(modern_menu_code)

    print("✅ All set! Run your client to see the new Plexus Sidebar design.")

if __name__ == "__main__":
    apply_premium_client_ui()