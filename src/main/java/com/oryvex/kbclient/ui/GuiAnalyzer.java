package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBSample;
import com.oryvex.kbclient.kb.KBYaml;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiScreen;
import org.lwjgl.input.Keyboard;
import org.lwjgl.input.Mouse;

public class GuiAnalyzer extends FadeScreen {
    private static int lastTab = 0;
    private static final int NT = 5;
    private static final String[] TAB_NAMES = { "Overview", "Samples", "Graph", "YAML", "Compare" };
    private static final String[] SHORT = {
        "ONE-POINT-SEVEN", "HORIZONTAL", "VERTICAL", "EXTRA-HORIZ", "EXTRA-VERT", "FRICTION",
        "Y-LIMIT", "DT OVERRIDE", "DT VALUE", "DYNAMIC-LIMIT", "LIMIT-HORIZ", "H-LIMIT"
    };

    public static void openTab(int t) { lastTab = Math.max(0, Math.min(NT - 1, t)); }

    private final KBTracker tracker;
    private final GuiScreen parent;
    private KBProfile profile;
    private KBProfile reference;
    private List<KBSample> samples = new ArrayList<KBSample>();
    private int tab;
    private int scroll;
    private int px, pw, y0, y1;
    private final UiButton[] tabs = new UiButton[NT];
    private UiButton pauseBtn;
    private String flash = "";
    private boolean flashGood = true;
    private long flashUntil;

    public GuiAnalyzer(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent = parent;
        this.tab = lastTab;
        refresh();
    }

    private void refresh() {
        profile = tracker.getProfile();
        reference = tracker.getReference();
        samples = tracker.snapshot();
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        pw = Math.min(this.width - 16, 460);
        px = (this.width - pw) / 2;
        y0 = 68;
        y1 = this.height - 34;

        int tw = Math.min(72, (pw - 16) / NT);
        for (int i = 0; i < NT; i++) {
            tabs[i] = new UiButton(10 + i, px + i * (tw + 4), 46, tw, 16, TAB_NAMES[i]).style(UiButton.TAB).delay(i * 40L);
            tabs[i].selected = (i == tab);
            this.buttonList.add(tabs[i]);
        }

        String[] labels = { "Import", "Copy YAML", "Export", "Reset", "Pause", "Reconnect", "Close" };
        int bw = Math.min(62, (pw - 20) / 7);
        int total = 7 * bw + 6 * 4;
        int bx = (this.width - total) / 2;
        for (int i = 0; i < 7; i++) {
            UiButton b = new UiButton(100 + i, bx + i * (bw + 4), this.height - 26, bw, 18, labels[i]).delay(120 + i * 40L);
            if (i == 0) b.style = UiButton.PRIMARY;
            if (i == 3) b.style = UiButton.DANGER;
            if (i == 4) pauseBtn = b;
            this.buttonList.add(b);
        }
    }

    @Override
    public void updateScreen() {
        super.updateScreen();
        refresh();
        if (pauseBtn != null) pauseBtn.displayString = tracker.isRecording() ? "Pause" : "Resume";
    }

    @Override
    public boolean doesGuiPauseGame() { return false; }

    private void setTab(int t) {
        tab = t;
        lastTab = t;
        scroll = 0;
        for (int i = 0; i < NT; i++) if (tabs[i] != null) tabs[i].selected = (i == t);
    }

    private void toast(String s, boolean good) {
        flash = s;
        flashGood = good;
        flashUntil = System.currentTimeMillis() + 3200;
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        if (b.id >= 10 && b.id < 10 + NT) { setTab(b.id - 10); return; }
        switch (b.id) {
            case 100: {
                KBYaml.Result r = tracker.importYaml(GuiScreen.getClipboardString());
                refresh();
                toast(r.parsed > 0 ? r.summary() : "Clipboard has no knockback YAML - copy a config first", r.complete());
                if (r.parsed > 0) setTab(4);
                break;
            }
            case 101:
                setClipboardString(profile.toYaml());
                toast("Detected YAML copied to clipboard", true);
                break;
            case 102:
                try {
                    File f = tracker.export();
                    toast("Saved " + f.getName(), true);
                } catch (Exception e) {
                    toast("Export failed: " + e.getMessage(), false);
                }
                break;
            case 103:
                tracker.reset();
                refresh();
                toast("Samples cleared", true);
                break;
            case 104:
                tracker.setRecording(!tracker.isRecording());
                break;
            case 105:
                if (this.mc != null && this.mc.thePlayer != null) this.mc.thePlayer.sendChatMessage("/findkb []");
                toast("Sent /findkb []", true);
                break;
            case 106:
                closeTo(parent);
                break;
            default:
                break;
        }
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        if (key == Keyboard.KEY_ESCAPE) { closeTo(parent); return; }
        if (key == Keyboard.KEY_RIGHT) setTab((tab + 1) % NT);
        else if (key == Keyboard.KEY_LEFT) setTab((tab + NT - 1) % NT);
        else if (key >= Keyboard.KEY_1 && key < Keyboard.KEY_1 + NT) setTab(key - Keyboard.KEY_1);
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

    private static int srcColor(int s) {
        switch (s) {
            case KBProfile.SRC_EST: return Theme.WARN;
            case KBProfile.SRC_MEAS: return Theme.GOOD;
            case KBProfile.SRC_IMP: return Theme.ACCENT2;
            default: return Theme.DIM;
        }
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        drawBackdrop(34);

        Draw.text("KNOCKBACK ANALYZER", px, 11, Theme.TEXT, 1.4f, true);
        Draw.text("Carbon / Spigot profile - detector + exact YAML import", px, 28, Theme.MUTED, 0.75f, false);

        boolean rec = tracker.isRecording();
        String st = (rec ? "LIVE" : "PAUSED") + "   " + profile.used + "/" + profile.total + " samples";
        int chipW = Draw.width(st, 0.85f) + 24;
        int chipX = px + pw - chipW;
        Draw.panel(chipX, 11, chipW, 16, 8, Theme.PANEL, Theme.BORDER);
        Draw.roundRect(chipX + 8, 17, 5, 5, 2, rec ? Theme.GOOD : Theme.WARN);
        Draw.text(st, chipX + 18, 15, Theme.SOFT, 0.85f, false);
        if (System.currentTimeMillis() < flashUntil) {
            Draw.right(flash, px + pw, 32, flashGood ? Theme.GOOD : Theme.WARN, 0.75f, false);
        } else {
            Draw.right(tracker.getServer(), px + pw, 32, Theme.DIM, 0.75f, false);
        }

        switch (tab) {
            case 0: drawOverview(); break;
            case 1: drawSamples(); break;
            case 2: drawGraph(); break;
            case 3: drawYaml(); break;
            default: drawCompare(); break;
        }

        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }

    // ---- overview ----------------------------------------------------------
    private void drawOverview() {
        KBProfile p = profile;
        int cols = 4, rows = 3, gap = 4;
        int cw = (pw - gap * (cols - 1)) / cols;
        int tipH = 30;
        int ch = Math.max(28, Math.min(40, (y1 - y0 - tipH - gap * rows) / rows));

        for (int i = 0; i < KBProfile.COUNT; i++) {
            int x = px + (i % cols) * (cw + gap);
            int y = y0 + (i / cols) * (ch + gap);
            boolean none = p.src[i] == KBProfile.SRC_NONE;
            int cc = none ? Theme.DIM : Draw.confColor(p.conf[i]);
            Draw.panel(x, y, cw, ch, 4, Theme.PANEL, Theme.BORDER);
            Draw.roundRect(x + 1, y + 5, 2, ch - 10, 1, cc);
            Draw.text(SHORT[i], x + 8, y + 5, Theme.MUTED, 0.68f, false);
            Draw.right(KBProfile.SRC_TAG[p.src[i]], x + cw - 6, y + 5, srcColor(p.src[i]), 0.62f, false);
            float vs = ch >= 38 ? 1.3f : 1f;
            Draw.text(p.valueText(i), x + 8, y + 14 + (ch >= 38 ? 1 : 0), none ? Theme.MUTED : Theme.TEXT, vs, true);
            Draw.bar(x + 8, y + ch - 6, cw - 16, 2, p.conf[i], Theme.PANEL3, cc);
        }

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
            String atk = !k.hasAttacker ? "--" : (k.sprintState == KBSample.AMBIGUOUS ? "???" : (k.attackerSprint ? "SPR" : "WLK"));
            int atkCol = k.sprintState == KBSample.AMBIGUOUS ? Theme.DIM : (k.attackerSprint ? Theme.WARN : Theme.GOOD);
            Draw.text(atk, px + cx[4], ry, atkCol, 0.85f, false);
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
        Draw.text("fitted HORIZONTAL / Y-LIMIT", px + 140, y0 + 7, Theme.MUTED, 0.8f, false);

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

    // ---- compare (detected vs imported reference) ---------------------------
    private void drawCompare() {
        Draw.panel(px, y0, pw, y1 - y0, 5, Theme.PANEL, Theme.BORDER);
        if (reference == null) {
            float cy = y0 + (y1 - y0) / 2f - 14;
            Draw.centered("No reference config loaded", px + pw / 2f, cy, Theme.SOFT, 1f, true);
            Draw.centered("Copy a Carbon knockback YAML, then press Import", px + pw / 2f, cy + 14, Theme.MUTED, 0.85f, false);
            Draw.centered("or use /kb import  |  /kb import file.yml  |  /kb sample", px + pw / 2f, cy + 26, Theme.DIM, 0.8f, false);
            return;
        }
        int[] cx = { 8, 150, 226, 302, 372 };
        String[] hd = { "KEY", "DETECTED", "REFERENCE", "DELTA", "STATUS" };
        int hy = y0 + 6;
        for (int i = 0; i < hd.length; i++) Draw.text(hd[i], px + cx[i], hy, Theme.ACCENT, 0.8f, false);
        Draw.rect(px + 6, hy + 11, pw - 12, 1, Theme.BORDER);

        int rowH = Math.max(9, Math.min(13, (y1 - y0 - 44) / KBProfile.COUNT));
        int match = 0, close = 0, off = 0;
        for (int i = 0; i < KBProfile.COUNT; i++) {
            int y = hy + 16 + i * rowH;
            if (i % 2 == 0) Draw.rect(px + 4, y - 2, pw - 8, rowH, 0x14FFFFFF);
            int cmp = profile.compare(reference, i);
            boolean hasDet = profile.src[i] != KBProfile.SRC_NONE;
            Draw.text(KBProfile.KEYS[i], px + cx[0], y, Theme.SOFT, 0.8f, false);
            Draw.text(hasDet ? profile.valueText(i) : profile.valueText(i) + " (def)", px + cx[1], y, hasDet ? Theme.TEXT : Theme.DIM, 0.8f, false);
            Draw.text(reference.src[i] == KBProfile.SRC_NONE ? "--" : reference.valueText(i), px + cx[2], y, Theme.ACCENT2, 0.8f, false);
            String delta = "-";
            if (cmp >= 0 && !KBProfile.isBool(i)) delta = String.format(Locale.ROOT, "%+.4f", profile.numeric(i) - reference.numeric(i));
            Draw.text(delta, px + cx[3], y, Theme.MUTED, 0.8f, false);
            String status;
            int sc;
            if (cmp == 0) { status = "MATCH"; sc = Theme.GOOD; match++; }
            else if (cmp == 1) { status = "CLOSE"; sc = Theme.WARN; close++; }
            else if (cmp == 2) { status = "OFF"; sc = Theme.BAD; off++; }
            else { status = "NO REF"; sc = Theme.DIM; }
            Draw.text(status, px + cx[4], y, sc, 0.8f, false);
        }
        int fy = y1 - 22;
        Draw.rect(px + 6, fy - 4, pw - 12, 1, Theme.BORDER);
        Draw.text(match + " match   " + close + " close   " + off + " off", px + 8, fy, Theme.SOFT, 0.85f, false);
        String imp = tracker.getLastImport();
        if (imp != null && !imp.isEmpty()) {
            Draw.text(fontRendererObj.trimStringToWidth(imp, (int) ((pw - 16) / 0.75f)), px + 8, fy + 10, Theme.MUTED, 0.75f, false);
        }
    }
}
