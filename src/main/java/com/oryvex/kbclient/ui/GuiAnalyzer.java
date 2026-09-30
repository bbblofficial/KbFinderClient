package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBSample;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiScreen;
import org.lwjgl.input.Keyboard;
import org.lwjgl.input.Mouse;

public class GuiAnalyzer extends GuiScreen {
    private static int lastTab = 0;

    private final KBTracker tracker;
    private final GuiScreen parent;
    private KBProfile profile;
    private List<KBSample> samples = new ArrayList<KBSample>();
    private int tab;
    private int scroll;
    private int px, pw, y0, y1;
    private final UiButton[] tabs = new UiButton[4];
    private UiButton pauseBtn;
    private String flash = "";
    private long flashUntil;

    public GuiAnalyzer(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent = parent;
        this.tab = lastTab;
        refresh();
    }

    private void refresh() {
        profile = tracker.getProfile();
        samples = tracker.snapshot();
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        pw = Math.min(this.width - 16, 440);
        px = (this.width - pw) / 2;
        y0 = 68;
        y1 = this.height - 34;

        String[] names = { "Overview", "Samples", "Graph", "YAML" };
        int tw = Math.min(72, (pw - 12) / 4);
        for (int i = 0; i < 4; i++) {
            tabs[i] = new UiButton(10 + i, px + i * (tw + 4), 46, tw, 16, names[i]).style(UiButton.TAB);
            tabs[i].selected = (i == tab);
            this.buttonList.add(tabs[i]);
        }

        String[] labels = { "Copy YAML", "Export", "Reset", "Pause", "Close" };
        int bw = Math.min(84, (pw - 16) / 5);
        int total = 5 * bw + 16;
        int bx = (this.width - total) / 2;
        for (int i = 0; i < 5; i++) {
            UiButton b = new UiButton(100 + i, bx + i * (bw + 4), this.height - 26, bw, 18, labels[i]);
            if (i == 0) b.style = UiButton.PRIMARY;
            if (i == 2) b.style = UiButton.DANGER;
            if (i == 3) pauseBtn = b;
            this.buttonList.add(b);
        }
    }

    @Override
    public void updateScreen() {
        refresh();
        if (pauseBtn != null) pauseBtn.displayString = tracker.isRecording() ? "Pause" : "Resume";
    }

    @Override
    public boolean doesGuiPauseGame() { return false; }

    private void setTab(int t) {
        tab = t;
        lastTab = t;
        scroll = 0;
        for (int i = 0; i < 4; i++) if (tabs[i] != null) tabs[i].selected = (i == t);
    }

    private void toast(String s) {
        flash = s;
        flashUntil = System.currentTimeMillis() + 2500;
    }

    private void close() {
        this.mc.displayGuiScreen(parent);
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        if (b.id >= 10 && b.id <= 13) { setTab(b.id - 10); return; }
        switch (b.id) {
            case 100:
                setClipboardString(profile.toYaml());
                toast("YAML copied to clipboard");
                break;
            case 101:
                try {
                    File f = tracker.export();
                    toast("Saved " + f.getName());
                } catch (Exception e) {
                    toast("Export failed: " + e.getMessage());
                }
                break;
            case 102:
                tracker.reset();
                refresh();
                toast("Samples cleared");
                break;
            case 103:
                tracker.setRecording(!tracker.isRecording());
                break;
            case 104:
                close();
                break;
            default:
                break;
        }
    }

    @Override
    protected void keyTyped(char c, int key) throws IOException {
        if (key == Keyboard.KEY_ESCAPE) { close(); return; }
        if (key == Keyboard.KEY_RIGHT) setTab((tab + 1) % 4);
        else if (key == Keyboard.KEY_LEFT) setTab((tab + 3) % 4);
        else if (key >= Keyboard.KEY_1 && key <= Keyboard.KEY_4) setTab(key - Keyboard.KEY_1);
        else if (key == Keyboard.KEY_UP) scroll = Math.max(0, scroll - 1);
        else if (key == Keyboard.KEY_DOWN) scroll++;
    }

    @Override
    public void handleMouseInput() throws IOException {
        super.handleMouseInput();
        int d = Mouse.getEventDWheel();
        if (d != 0) {
            scroll += d > 0 ? -2 : 2;
            if (scroll < 0) scroll = 0;
        }
    }

    // ------------------------------------------------------------------------
    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        this.drawGradientRect(0, 0, this.width, this.height, Theme.BG0, Theme.BG1);
        Draw.particles(this.width, this.height, 34, 0x22D3EE, 0.22f);

        // header
        Draw.text("KNOCKBACK ANALYZER", px, 11, Theme.TEXT, 1.4f, true);
        Draw.text("Carbon / Spigot profile estimator - live from velocity packets", px, 28, Theme.MUTED, 0.75f, false);

        boolean rec = tracker.isRecording();
        String st = (rec ? "LIVE" : "PAUSED") + "   " + profile.used + "/" + profile.total + " samples";
        int chipW = Draw.width(st, 0.85f) + 24;
        int chipX = px + pw - chipW;
        Draw.panel(chipX, 11, chipW, 16, 8, Theme.PANEL, Theme.BORDER);
        Draw.roundRect(chipX + 8, 17, 5, 5, 2, rec ? Theme.GOOD : Theme.WARN);
        Draw.text(st, chipX + 18, 15, Theme.SOFT, 0.85f, false);
        if (System.currentTimeMillis() < flashUntil) {
            Draw.right(flash, px + pw, 32, Theme.GOOD, 0.8f, false);
        } else {
            Draw.right(tracker.getServer(), px + pw, 32, Theme.DIM, 0.75f, false);
        }

        switch (tab) {
            case 0: drawOverview(); break;
            case 1: drawSamples(); break;
            case 2: drawGraph(); break;
            default: drawYaml(); break;
        }

        super.drawScreen(mouseX, mouseY, partialTicks);
    }

    // ---- overview ----------------------------------------------------------
    private static String yn(boolean b) { return b ? "true" : "false"; }

    private void drawOverview() {
        KBProfile p = profile;
        boolean has = p.hasData;
        String[] labels = {
            "ONE-POINT-SEVEN", "HORIZONTAL", "VERTICAL", "EXTRA-HORIZONTAL",
            "EXTRA-VERTICAL", "FRICTION", "Y-LIMIT", "H-LIMIT",
            "DYNAMIC-LIMIT", "LIMIT-HORIZONTAL", "DAMAGE-TICKS.OVERRIDE", "DAMAGE-TICKS.VALUE"
        };
        String[] vals = {
            yn(p.onePointSeven), KBProfile.f(p.horizontal, 4), KBProfile.f(p.vertical, 4), KBProfile.f(p.extraHorizontal, 4),
            KBProfile.f(p.extraVertical, 4), KBProfile.f(p.friction, 3), KBProfile.f(p.yLimit, 3), KBProfile.f(p.hLimit, 3),
            yn(p.dynamicLimit), yn(p.limitHorizontal), yn(p.damageTicksOverride), String.valueOf(p.damageTicksValue)
        };
        double[] conf = { p.cOps, p.cH, p.cV, p.cEH, p.cEV, p.cF, p.cYL, p.cHL, p.cDyn, p.cLimH, p.cDT, p.cDT };

        int cols = 4, rows = 3, gap = 4;
        int cw = (pw - gap * (cols - 1)) / cols;
        int avail = y1 - y0;
        int tipH = 30;
        int ch = Math.max(28, Math.min(40, (avail - tipH - gap * rows) / rows));

        for (int i = 0; i < 12; i++) {
            int x = px + (i % cols) * (cw + gap);
            int y = y0 + (i / cols) * (ch + gap);
            int cc = (has || i >= 10) ? Draw.confColor(conf[i]) : Theme.DIM;
            Draw.panel(x, y, cw, ch, 4, Theme.PANEL, Theme.BORDER);
            Draw.roundRect(x + 1, y + 5, 2, ch - 10, 1, cc);
            Draw.text(labels[i], x + 8, y + 5, Theme.MUTED, 0.68f, false);
            String v = (has || i >= 10) ? vals[i] : "--";
            if (i >= 10 && !has && p.cDT == 0) v = vals[i];
            float vs = ch >= 38 ? 1.3f : 1f;
            Draw.text(v, x + 8, y + 14 + (ch >= 38 ? 1 : 0), Theme.TEXT, vs, true);
            Draw.bar(x + 8, y + ch - 6, cw - 16, 2, has || i >= 10 ? conf[i] : 0, Theme.PANEL3, cc);
        }

        // tip strip
        int ty = y0 + rows * (ch + gap);
        int th = Math.min(tipH, y1 - ty);
        if (th >= 18) {
            Draw.panel(px, ty, pw, th, 4, Theme.PANEL, Theme.BORDER);
            Draw.roundRect(px + 6, ty + 6, 24, 10, 3, Theme.ACCENT_DK);
            Draw.centered("TIP", px + 18, ty + 8, Theme.TEXT, 0.75f, false);
            String tip;
            if (p.notes.isEmpty()) tip = "Looking good - keep collecting varied hits to raise confidence.";
            else tip = p.notes.get((int) ((System.currentTimeMillis() / 4000L) % p.notes.size()));
            List<String> lines = fontRendererObj.listFormattedStringToWidth(tip, pw - 50);
            for (int i = 0; i < lines.size() && i < 2; i++) {
                Draw.text(lines.get(i), px + 36, ty + 5 + i * 10, Theme.SOFT, 1f, false);
            }
        }
    }

    // ---- samples -----------------------------------------------------------
    private void drawSamples() {
        Draw.panel(px, y0, pw, y1 - y0, 5, Theme.PANEL, Theme.BORDER);
        int[] cx = { 8, 34, 88, 142, 196, 230, 264, 304 };
        String[] hd = { "#", "H", "V", "PRE-H", "ATK", "GND", "DIST", "ATTACKER" };
        int hy = y0 + 6;
        for (int i = 0; i < hd.length; i++) Draw.text(hd[i], px + cx[i], hy, Theme.ACCENT, 0.8f, false);
        Draw.rect(px + 6, hy + 11, pw - 12, 1, Theme.BORDER);

        int n = samples.size();
        if (n == 0) {
            Draw.centered("No samples yet - get hit by another player.", px + pw / 2f, y0 + (y1 - y0) / 2f - 4, Theme.MUTED, 1f, false);
            return;
        }
        int rowH = 10;
        int rows = Math.max(1, (y1 - (hy + 15) - 4) / rowH);
        scroll = Math.max(0, Math.min(scroll, Math.max(0, n - rows)));
        for (int r = 0; r < rows; r++) {
            int idx = n - 1 - (scroll + r);
            if (idx < 0) break;
            KBSample k = samples.get(idx);
            int ry = hy + 15 + r * rowH;
            if (r % 2 == 0) Draw.rect(px + 4, ry - 1, pw - 8, rowH, 0x14FFFFFF);
            Draw.text(String.valueOf(k.id), px + cx[0], ry, Theme.MUTED, 0.85f, false);
            Draw.text(KBProfile.f(k.h, 4), px + cx[1], ry, Theme.TEXT, 0.85f, false);
            Draw.text(KBProfile.f(k.vy, 4), px + cx[2], ry, Theme.TEXT, 0.85f, false);
            Draw.text(KBProfile.f(k.pH, 3), px + cx[3], ry, Theme.SOFT, 0.85f, false);
            Draw.text(k.hasAttacker ? (k.attackerSprint ? "SPR" : "WLK") : "--", px + cx[4], ry,
                    k.attackerSprint ? Theme.WARN : Theme.GOOD, 0.85f, false);
            Draw.text(k.victimGround ? "gnd" : "air", px + cx[5], ry, k.victimGround ? Theme.SOFT : Theme.ACCENT2, 0.85f, false);
            Draw.text(KBProfile.f(k.distance, 1), px + cx[6], ry, Theme.SOFT, 0.85f, false);
            String nm = fontRendererObj.trimStringToWidth(k.attacker, Math.max(10, pw - cx[7] - 10));
            Draw.text(nm, px + cx[7], ry, Theme.MUTED, 0.85f, false);
        }
        if (n > rows) {
            int bh = y1 - y0 - 8;
            int th = Math.max(10, bh * rows / n);
            int ty = y0 + 4 + (int) ((bh - th) * (scroll / (double) Math.max(1, n - rows)));
            Draw.roundRect(px + pw - 5, ty, 2, th, 1, Theme.BORDER_HI);
        }
    }

    // ---- graph -------------------------------------------------------------
    private void drawGraph() {
        Draw.panel(px, y0, pw, y1 - y0, 5, Theme.PANEL, Theme.BORDER);
        Draw.roundRect(px + 10, y0 + 8, 6, 6, 2, Theme.ACCENT);
        Draw.text("Horizontal", px + 20, y0 + 7, Theme.SOFT, 0.8f, false);
        Draw.roundRect(px + 72, y0 + 8, 6, 6, 2, Theme.ACCENT2);
        Draw.text("Vertical", px + 82, y0 + 7, Theme.SOFT, 0.8f, false);
        Draw.dashedH(px + 126, y0 + 11, 10, Theme.WARN);
        Draw.text("fitted H / Y-LIMIT", px + 140, y0 + 7, Theme.MUTED, 0.8f, false);

        int cx0 = px + 30, cx1 = px + pw - 10;
        int cy0 = y0 + 22, cy1 = y1 - 12;
        int chartW = cx1 - cx0, chartH = cy1 - cy0;
        if (chartH < 20 || chartW < 40) return;

        int n = samples.size();
        double max = 0.6;
        for (KBSample k : samples) { max = Math.max(max, Math.max(k.h, Math.abs(k.vy))); }
        max = Math.ceil(max * 10.0) / 10.0;

        for (int g = 0; g <= 4; g++) {
            int gy = cy1 - (int) (chartH * g / 4.0);
            Draw.rect(cx0, gy, chartW, 1, g == 0 ? Theme.BORDER_HI : Theme.BORDER);
            Draw.right(KBProfile.f(max * g / 4.0, 2), cx0 - 4, gy - 4, Theme.DIM, 0.7f, false);
        }
        if (n == 0) {
            Draw.centered("No samples yet", (cx0 + cx1) / 2f, (cy0 + cy1) / 2f, Theme.MUTED, 1f, false);
            return;
        }
        int show = Math.min(n, Math.max(1, chartW / 7));
        double slot = chartW / (double) show;
        int barW = Math.max(1, (int) ((slot - 2) / 2));
        for (int i = 0; i < show; i++) {
            KBSample k = samples.get(n - show + i);
            int bx = cx0 + (int) (i * slot) + 1;
            int hh = (int) (chartH * Math.min(1.0, k.h / max));
            int vh = (int) (chartH * Math.min(1.0, Math.abs(k.vy) / max));
            if (hh > 0) Draw.roundRect(bx, cy1 - hh, barW, hh, 1, k.attackerSprint ? Draw.lerp(Theme.ACCENT, Theme.WARN, 0.5f) : Theme.ACCENT);
            if (vh > 0) Draw.roundRect(bx + barW, cy1 - vh, barW, vh, 1, Theme.ACCENT2);
        }
        if (profile.hasData) {
            int hy = cy1 - (int) (chartH * Math.min(1.0, profile.horizontal / max));
            int yy = cy1 - (int) (chartH * Math.min(1.0, profile.yLimit / max));
            Draw.dashedH(cx0, hy, chartW, Theme.WARN);
            Draw.dashedH(cx0, yy, chartW, Theme.ACCENT2);
        }
    }

    // ---- yaml --------------------------------------------------------------
    private void drawYaml() {
        Draw.panel(px, y0, pw, y1 - y0, 5, Theme.PANEL, Theme.BORDER);
        String[] lines = profile.toYaml().split("\n");
        int rowH = 9;
        int rows = Math.max(1, (y1 - y0 - 12) / rowH);
        scroll = Math.max(0, Math.min(scroll, Math.max(0, lines.length - rows)));
        for (int r = 0; r < rows; r++) {
            int idx = scroll + r;
            if (idx >= lines.length) break;
            String ln = lines[idx];
            int y = y0 + 7 + r * rowH;
            int indent = 0;
            while (indent < ln.length() && ln.charAt(indent) == ' ') indent++;
            int x = px + 10 + indent * 3;
            String body = ln.substring(indent);
            if (body.startsWith("#")) {
                Draw.text(body, x, y, Theme.DIM, 0.85f, false);
            } else {
                int c = body.indexOf(':');
                if (c > 0) {
                    String key = body.substring(0, c + 1);
                    String val = body.substring(c + 1);
                    Draw.text(key, x, y, Theme.ACCENT, 0.85f, false);
                    String vt = val.trim();
                    int vc = (vt.equals("true") || vt.equals("false")) ? Theme.ACCENT2 : Theme.TEXT;
                    Draw.text(val, x + Draw.width(key, 0.85f), y, vc, 0.85f, false);
                }
            }
        }
    }
}
