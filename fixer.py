import os

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write_file(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Restored: {os.path.basename(path)}")

base_dir = os.path.dirname(os.path.abspath(__file__))
root_pkg = os.path.join(base_dir, "src", "main", "java", "com", "oryvex", "kbclient")
kb_pkg = os.path.join(root_pkg, "kb")

# ==============================================================================
# 1. KBEstimator.java  (ORIGINAL — coarse+fine grid, plateau, solve, capped)
# ==============================================================================
kb_estimator = r"""package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Solver for the Carbon / Spigot knockback model.
 *
 *   horizontal:  v_new = v_old / FRICTION + dir * (HORIZONTAL [+ EXTRA-HORIZONTAL if attacker sprints])
 *   vertical:    y_new = y_old / FRICTION + VERTICAL   [+ EXTRA-VERTICAL if attacker sprints]  -> clamped to Y-LIMIT
 *
 * (A) FRICTION: coarse + fine grid search on the within-group residual variance,
 * (B) plateau detection for Y-LIMIT / H-LIMIT, (C) robust medians per group,
 * (D) hit-gap analysis for DAMAGE-TICKS. Hits whose attacker sprint state was
 * changing (W-tap) are excluded as ambiguous.
 */
public final class KBEstimator {
    private KBEstimator() {}

    private static double conf(double n) { return 1.0 - Math.exp(-n / 3.0); }
    private static double r4(double v) { return Math.rint(v * 10000.0) / 10000.0; }

    private static double median(List<Double> v) {
        if (v.isEmpty()) return 0;
        List<Double> c = new ArrayList<Double>(v);
        Collections.sort(c);
        int n = c.size();
        return (n % 2 == 1) ? c.get(n / 2) : (c.get(n / 2 - 1) + c.get(n / 2)) / 2.0;
    }

    private static double max(List<Double> v) {
        double m = -Double.MAX_VALUE;
        for (double d : v) m = Math.max(m, d);
        return m;
    }

    private static double std(List<Double> v) {
        if (v.size() < 2) return 0;
        double m = 0;
        for (double d : v) m += d;
        m /= v.size();
        double s = 0;
        for (double d : v) s += (d - m) * (d - m);
        return Math.sqrt(s / (v.size() - 1));
    }

    private static double spread(List<Double> v) {
        if (v.isEmpty()) return 0;
        double lo = Double.MAX_VALUE, hi = -Double.MAX_VALUE;
        for (double d : v) { lo = Math.min(lo, d); hi = Math.max(hi, d); }
        return hi - lo;
    }

    private static double cost(List<KBSample> fit, double f) {
        double inv = 1.0 / f;
        double[] sa = new double[2], sa2 = new double[2], sy = new double[2], sy2 = new double[2];
        int[] na = new int[2], ny = new int[2];
        double orth = 0;
        for (KBSample k : fit) {
            int g = k.attackerSprint ? 1 : 0;
            double rx = k.vx - k.px * inv, rz = k.vz - k.pz * inv;
            double along = rx * k.ux + rz * k.uz;
            double ortho = -rx * k.uz + rz * k.ux;
            orth += ortho * ortho;
            sa[g] += along; sa2[g] += along * along; na[g]++;
            double ry = k.vy - k.py * inv;
            sy[g] += ry; sy2[g] += ry * ry; ny[g]++;
        }
        double c = orth;
        for (int g = 0; g < 2; g++) {
            if (na[g] > 0) c += sa2[g] - sa[g] * sa[g] / na[g];
            if (ny[g] > 0) c += sy2[g] - sy[g] * sy[g] / ny[g];
        }
        return c / Math.max(1, fit.size());
    }

    /** returns {base, extra, confBase, confExtra, spread, lowerBoundFlag} */
    private static double[] solve(List<Double> w, List<Double> s, List<Double> wC, List<Double> sC, double defExtra) {
        double base, extra, cB, cE, spr = 0, lb = 0;
        if (!w.isEmpty()) {
            base = median(w); cB = conf(w.size()); spr = std(w);
            if (!wC.isEmpty() && max(wC) > base) { base = max(wC); lb = 1; }
            if (!s.isEmpty()) { extra = median(s) - base; cE = conf(Math.min(w.size(), s.size())); }
            else if (!sC.isEmpty()) { extra = max(sC) - base; cE = 0.25; lb = 1; }
            else { extra = defExtra; cE = 0; }
        } else if (!s.isEmpty()) {
            extra = defExtra; base = median(s) - extra; cB = 0.25; cE = 0; spr = std(s);
        } else if (!wC.isEmpty() || !sC.isEmpty()) {
            extra = defExtra;
            if (!wC.isEmpty()) base = max(wC); else base = max(sC) - extra;
            cB = 0.2; cE = 0; lb = 1;
        } else {
            base = 0; extra = defExtra; cB = 0; cE = 0;
        }
        return new double[] { Math.max(0, base), Math.max(0, extra), cB, cE, spr, lb };
    }

    public static KBProfile calculate(List<KBSample> all) {
        KBProfile p = new KBProfile();
        p.total = (all == null) ? 0 : all.size();
        if (all == null || all.isEmpty()) {
            p.notes.add("Waiting for knockback - get hit by another player.");
            return p;
        }

        int ench = 0, amb = 0;
        List<KBSample> s = new ArrayList<KBSample>();
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (k.sprintState == KBSample.AMBIGUOUS) { amb++; continue; }
            if (k.attackerKb > 0) { ench++; continue; }
            if (k.h < 0.0005 && Math.abs(k.vy) < 0.0005) continue;
            s.add(k);
        }

        int n = s.size();
        p.used = n;
        p.ambiguous = amb;
        if (ench > 0) p.notes.add("Ignored " + ench + " hit(s) from Knockback-enchanted weapons.");
        if (amb > 0) p.notes.add("Ignored " + amb + " hit(s) where the attacker's sprint state was changing (W-tap).");

        detectDamageTicks(all, p);

        if (n == 0) {
            p.notes.add("No usable hits yet (need a nearby attacking player).");
            return p;
        }

        p.hasData = true;
        for (KBSample k : s) { if (k.attackerSprint) p.sprint++; else p.walk++; }

        // ---- plateau detection
        double yMax = -10, hMax = 0;
        for (KBSample k : s) { yMax = Math.max(yMax, k.vy); hMax = Math.max(hMax, k.h); }
        boolean[] hPl = new boolean[n], yPl = new boolean[n];
        int hPlN = 0, yPlN = 0;
        for (int i = 0; i < n; i++) {
            KBSample k = s.get(i);
            if (k.h >= hMax - 0.002) { hPl[i] = true; hPlN++; }
            if (k.vy >= yMax - 0.0015) { yPl[i] = true; yPlN++; }
        }
        boolean hMulti = hPlN >= 2 && hPlN < n;
        boolean yMulti = yPlN >= 2 && yPlN < n;

        // ---- (A) FRICTION
        List<KBSample> fit = new ArrayList<KBSample>();
        for (int i = 0; i < n; i++) {
            if ((hMulti && hPl[i]) || (yMulti && yPl[i])) continue;
            fit.add(s.get(i));
        }
        if (fit.size() < 4) fit = s;

        int moving = 0;
        for (KBSample k : fit) if (k.pH > 0.08) moving++;

        double F = 2.0;
        if (moving >= 3) {
            double best = Double.MAX_VALUE, bestF = 2.0;
            for (double f = 1.0; f <= 6.0001; f += 0.02) {
                double c = cost(fit, f);
                if (c < best - 1e-12) { best = c; bestF = f; }
            }
            double lo = Math.max(1.0, bestF - 0.02), hi = Math.min(6.0, bestF + 0.02);
            for (double f = lo; f <= hi + 1e-9; f += 0.001) {
                double c = cost(fit, f);
                if (c < best - 1e-12) { best = c; bestF = f; }
            }
            double c2 = cost(fit, 2.0);
            boolean informative = cost(fit, 1.5) - best > 1e-5 && cost(fit, 3.0) - best > 1e-5;
            if (informative && Math.abs(bestF - 2.0) <= 0.02) {
                F = 2.0;
                p.frictionMeasured = true;
                p.mark(KBProfile.I_F, conf(moving / 2.0));
            } else if (best < c2 * 0.6 && c2 - best > 1e-5) {
                F = bestF;
                p.frictionMeasured = true;
                double cf = conf(moving / 2.0);
                if (F <= 1.03 || F >= 5.97) { cf *= 0.4; p.notes.add("FRICTION hit the search boundary - result is unreliable."); }
                p.mark(KBProfile.I_F, cf);
            } else {
                p.mark(KBProfile.I_F, 0.35);
                p.notes.add("FRICTION matches the default 2.0 (no evidence of another value).");
            }
        } else {
            p.mark(KBProfile.I_F, 0);
            p.notes.add("FRICTION not measured - get hit while walking/strafing (pre-hit speed > 0.08).");
        }
        F = Math.round(F * 1000.0) / 1000.0;
        p.friction = F;

        // ---- (B) which plateaus are genuinely clamped?
        boolean hCapped = false, yCapped = false;
        if (hMulti) {
            List<Double> pa = new ArrayList<Double>();
            for (int i = 0; i < n; i++) if (hPl[i]) { KBSample k = s.get(i); pa.add((k.px * k.ux + k.pz * k.uz) / F); }
            hCapped = spread(pa) >= 0.03;
        }
        if (yMulti) {
            List<Double> pa = new ArrayList<Double>();
            for (int i = 0; i < n; i++) if (yPl[i]) pa.add(s.get(i).py / F);
            yCapped = spread(pa) >= 0.03;
        }

        // ---- (C) residual groups
        List<Double> hw = new ArrayList<Double>(), hs = new ArrayList<Double>();
        List<Double> hwC = new ArrayList<Double>(), hsC = new ArrayList<Double>();
        List<Double> vw = new ArrayList<Double>(), vs = new ArrayList<Double>();
        List<Double> vwC = new ArrayList<Double>(), vsC = new ArrayList<Double>();
        double inv = 1.0 / F;
        for (int i = 0; i < n; i++) {
            KBSample k = s.get(i);
            double rx = k.vx - k.px * inv, rz = k.vz - k.pz * inv;
            double along = rx * k.ux + rz * k.uz;
            double ry = k.vy - k.py * inv;
            boolean hc = hCapped && hPl[i], yc = yCapped && yPl[i];
            if (k.attackerSprint) { (hc ? hsC : hs).add(along); (yc ? vsC : vs).add(ry); }
            else { (hc ? hwC : hw).add(along); (yc ? vwC : vw).add(ry); }
        }

        double[] hr = solve(hw, hs, hwC, hsC, 0.5);
        p.horizontal = r4(hr[0]); p.extraHorizontal = r4(hr[1]); p.hSpread = hr[4];
        p.mark(KBProfile.I_H, hr[2]); p.mark(KBProfile.I_EH, hr[3]);
        if (hr[5] > 0) p.notes.add("HORIZONTAL/EXTRA-HORIZONTAL are lower bounds (hits were clamped by H-LIMIT).");

        double[] vr = solve(vw, vs, vwC, vsC, 0.0);
        p.vertical = r4(vr[0]); p.extraVertical = r4(vr[1]); p.vSpread = vr[4];
        p.mark(KBProfile.I_V, vr[2]); p.mark(KBProfile.I_EV, vr[3]);
        if (vr[5] > 0) p.notes.add("VERTICAL is a lower bound (clamped by Y-LIMIT). Get hit while FALLING (negative Y motion) to unclamp it.");

        if (p.walk == 0) p.notes.add("Need hits from a NON-sprinting attacker to separate HORIZONTAL from EXTRA-HORIZONTAL.");
        if (p.sprint == 0) p.notes.add("Need hits from a SPRINTING attacker to measure EXTRA-HORIZONTAL / EXTRA-VERTICAL.");

        // ---- limits
        p.yLimit = r4(yMax);
        if (yCapped) p.mark(KBProfile.I_YL, conf(yPlN / 1.5));
        else {
            p.mark(KBProfile.I_YL, 0.25);
            p.notes.add("Y-LIMIT is only the highest vertical knockback seen - get hit in mid-air at different heights to confirm the cap.");
        }

        p.hLimit = r4(hMax);
        p.limitHorizontal = hCapped;
        p.mark(KBProfile.I_LIMH, hCapped ? conf(hPlN / 1.5) : (moving >= 3 ? 0.55 : 0.15));
        p.mark(KBProfile.I_HL, hCapped ? conf(hPlN / 1.5) : 0.15);
        if (!hCapped) p.notes.add("H-LIMIT looks inactive (never clamped): shown value is the largest horizontal hit seen. Use /kb import for the exact file value.");

        // ---- DYNAMIC-LIMIT
        int airHigh = 0;
        boolean dyn = false;
        for (KBSample k : all) {
            if (!k.hasAttacker || k.victimGround) continue;
            if (k.py >= p.yLimit - 0.06) {
                airHigh++;
                if (Math.abs(k.vy) < 0.0005 && k.h > 0.0005) dyn = true;
            }
        }
        p.dynamicLimit = dyn;
        p.mark(KBProfile.I_DYN, dyn ? 0.6 : (airHigh >= 2 ? 0.5 : 0.12));

        // ---- ONE-POINT-SEVEN
        if (p.walk > 0 && p.sprint > 0) {
            p.onePointSeven = p.extraHorizontal < 0.02 && p.extraVertical < 0.02;
            p.mark(KBProfile.I_OPS, 0.35);
        } else {
            p.onePointSeven = false;
            p.mark(KBProfile.I_OPS, 0.08);
        }

        return p;
    }

    /** hits can land again once noDamageTicks <= VALUE/2, so shortest gap g gives VALUE = 2g (or 2g-1). */
    private static void detectDamageTicks(List<KBSample> all, KBProfile p) {
        List<Integer> iv = new ArrayList<Integer>();
        KBSample prev = null;
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (prev != null && prev.attacker.equals(k.attacker)) {
                long d = k.tick - prev.tick;
                if (d >= 1 && d <= 60) iv.add((int) d);
            }
            prev = k;
        }

        p.damageTicksValue = 20;
        p.damageTicksOverride = false;
        if (iv.isEmpty()) {
            p.mark(KBProfile.I_DTO, 0);
            p.mark(KBProfile.I_DTV, 0);
            p.notes.add("DAMAGE-TICKS unknown - have someone hit you rapidly.");
            return;
        }

        Collections.sort(iv);
        int m = iv.size() >= 4 ? iv.get(1) : iv.get(0);
        if (m >= 10) {
            p.mark(KBProfile.I_DTO, iv.size() >= 3 ? 0.45 : 0.2);
            p.mark(KBProfile.I_DTV, 0);
            p.notes.add("Hit gap " + m + " ticks = vanilla 20. DAMAGE-TICKS.VALUE is not observable while OVERRIDE is false - use /kb import.");
        } else {
            p.damageTicksValue = Math.max(2, m * 2);
            p.damageTicksOverride = true;
            double c = iv.size() >= 4 ? 0.75 : 0.45;
            p.mark(KBProfile.I_DTO, c);
            p.mark(KBProfile.I_DTV, c * 0.8);
            p.notes.add("Shortest hit gap " + m + " ticks -> DAMAGE-TICKS.VALUE is " + (m * 2) + " or " + (m * 2 - 1) + ".");
        }
    }
}
"""

# ==============================================================================
# 2. KBTracker.java  (ORIGINAL — MAX_SAMPLES=120, score-based attacker, CSV export)
# ==============================================================================
kb_tracker = r"""package com.oryvex.kbclient;

import com.oryvex.kbclient.kb.KBEstimator;
import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBSample;
import com.oryvex.kbclient.kb.KBYaml;
import com.oryvex.kbclient.ui.Hud;
import com.oryvex.kbclient.ui.Theme;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.enchantment.EnchantmentHelper;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.util.ChatComponentText;

/** Collects knockback samples (main thread only), keeps a live profile and an imported reference. */
public class KBTracker {
    public static final int MAX_SAMPLES = 120;
    private final List<KBSample> samples = new ArrayList<KBSample>();
    private final Map<Integer, Integer> sprintBits = new HashMap<Integer, Integer>();
    private KBProfile profile = new KBProfile();
    private KBProfile reference;
    private String lastImport = "";
    private KBSample last;
    private boolean recording = true;
    private int goal = 0;
    private int sessionHits = 0;
    private int nextId = 1;
    private long tick = 0;
    private String server = "-";

    public KBTracker() {
        profile.notes.add("Waiting for knockback - get hit by another player.");
    }

    /** per client tick: remember the last 3 ticks of every player's sprint flag */
    public synchronized void tick() {
        tick++;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.theWorld == null) return;
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            int id = e.getEntityId();
            int s = e.isSprinting() ? 1 : 0;
            Integer b = sprintBits.get(id);
            int nb = (b == null) ? (s == 1 ? 0x7 : 0) : (((b << 1) | s) & 0x7);
            sprintBits.put(id, nb);
        }
    }

    public synchronized KBProfile getProfile() { return profile; }
    public synchronized KBProfile getReference() { return reference; }
    public synchronized String getLastImport() { return lastImport; }
    public synchronized KBSample getLast() { return last; }
    public synchronized List<KBSample> snapshot() { return new ArrayList<KBSample>(samples); }
    public synchronized boolean isRecording() { return recording; }
    public synchronized void setRecording(boolean r) { recording = r; }
    public synchronized int getGoal() { return goal; }
    public synchronized int getSessionHits() { return sessionHits; }
    public synchronized String getServer() { return server; }

    public synchronized void reset() {
        samples.clear();
        last = null;
        sessionHits = 0;
        profile = new KBProfile();
        profile.notes.add("Waiting for knockback - get hit by another player.");
    }

    public synchronized void onConnect(String name) {
        reset();
        sprintBits.clear();
        server = name;
        recording = true;
        goal = 0;
    }

    public synchronized void startGoal(int hits) {
        reset();
        goal = Math.max(1, hits);
        recording = true;
        chat(Theme.S + "b[KB] " + Theme.S + "7Recording " + Theme.S + "e" + goal + Theme.S + "7 hits. Get hit by sprinting AND walking players.");
    }

    // ---- YAML reference ------------------------------------------------------
    public synchronized KBYaml.Result importYaml(String text) {
        KBYaml.Result r = KBYaml.parse(text);
        if (r.parsed > 0) {
            reference = r.profile;
            lastImport = r.summary();
            chat(Theme.S + "a[KB] Imported: " + Theme.S + "f" + r.summary());
            if (!r.unknown.isEmpty()) chat(Theme.S + "7Ignored unknown keys: " + r.unknown);
        } else {
            lastImport = "nothing imported";
            chat(Theme.S + "c[KB] No knockback keys found. Copy a YAML config first.");
        }
        return r;
    }

    public synchronized void clearReference() {
        reference = null;
        lastImport = "";
    }

    /** Must be called on the client main thread, BEFORE the packet is applied. */
    public synchronized void capture(int rawX, int rawY, int rawZ) {
        Minecraft mc = Minecraft.getMinecraft();
        EntityPlayerSP me = mc.thePlayer;
        if (!recording || me == null || mc.theWorld == null) return;

        double vx = rawX / 8000.0, vy = rawY / 8000.0, vz = rawZ / 8000.0;
        double h = Math.sqrt(vx * vx + vz * vz);

        EntityPlayer attacker = null;
        double bestScore = -1.0e9;
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            if (e == me || e.isDead) continue;
            double dist = me.getDistanceToEntity(e);
            if (dist > 7.0) continue;
            double dx = me.posX - e.posX, dz = me.posZ - e.posZ;
            double dh = Math.sqrt(dx * dx + dz * dz);
            double score = -dist * 0.05;
            if (h > 0.05 && dh > 0.001) score += (vx * dx + vz * dz) / (h * dh);
            if (score > bestScore) { bestScore = score; attacker = e; }
        }

        boolean has = attacker != null;
        double ux = 0, uz = 0, dist = 0;
        int state = KBSample.WALK;
        int kb = 0;
        String name = "?";

        if (has) {
            double dx = me.posX - attacker.posX, dz = me.posZ - attacker.posZ;
            double dh = Math.sqrt(dx * dx + dz * dz);
            if (dh > 0.001) { ux = dx / dh; uz = dz / dh; }
            else if (h > 0.001) { ux = vx / h; uz = vz / h; }

            Integer bits = sprintBits.get(attacker.getEntityId());
            if (bits == null) state = attacker.isSprinting() ? KBSample.SPRINT : KBSample.WALK;
            else if (bits == 0x7) state = KBSample.SPRINT;
            else if (bits == 0) state = KBSample.WALK;
            else state = KBSample.AMBIGUOUS;

            try { kb = EnchantmentHelper.getKnockbackModifier(attacker); } catch (Throwable ignored) { }
            name = attacker.getName();
            dist = me.getDistanceToEntity(attacker);
        }

        KBSample s = new KBSample(nextId++, tick, vx, vy, vz,
                me.motionX, me.motionY, me.motionZ, me.isSprinting(), me.onGround,
                has, state, kb, ux, uz, dist, name);
        samples.add(s);
        while (samples.size() > MAX_SAMPLES) samples.remove(0);
        last = s;
        profile = KBEstimator.calculate(samples);

        String tag = !has ? "no attacker" : (state == KBSample.AMBIGUOUS ? "W-TAP?" : (state == KBSample.SPRINT ? "SPRINT" : "WALK"));
        int col = !has ? Theme.DIM : (state == KBSample.AMBIGUOUS ? Theme.DIM : (state == KBSample.SPRINT ? Theme.WARN : Theme.GOOD));
        Hud.push("Hit #" + s.id + "  H " + KBProfile.f(h, 4) + "  V " + KBProfile.f(vy, 4) + "  " + tag, col);

        if (goal > 0) {
            sessionHits++;
            if (sessionHits >= goal) {
                recording = false;
                goal = 0;
                printResults();
            }
        }
    }

    public void chat(String msg) {
        EntityPlayerSP p = Minecraft.getMinecraft().thePlayer;
        if (p != null) p.addChatMessage(new ChatComponentText(msg));
    }

    public void printResults() {
        KBProfile p = profile;
        String b = Theme.S + "b", g = Theme.S + "7", w = Theme.S + "f";
        chat(b + "=========== KB PROFILE ===========");
        chat(g + "HORIZONTAL: " + w + p.valueText(KBProfile.I_H) + g + "   EXTRA-H: " + w + p.valueText(KBProfile.I_EH));
        chat(g + "VERTICAL: " + w + p.valueText(KBProfile.I_V) + g + "   EXTRA-V: " + w + p.valueText(KBProfile.I_EV));
        chat(g + "FRICTION: " + w + p.valueText(KBProfile.I_F) + g + "   Y-LIMIT: " + w + p.valueText(KBProfile.I_YL));
        chat(g + "DAMAGE-TICKS: " + w + p.damageTicksValue + g + " (override " + p.damageTicksOverride + ")");
        chat(Theme.S + "aOpen the analyzer with [Right Shift] or /kb");
    }

    public synchronized File export() throws IOException {
        File dir = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("Cannot create " + dir);
        String ts = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        File yml = new File(dir, "knockback-" + ts + ".yml");
        Files.write(yml.toPath(), (profile.toYaml() + "\n").getBytes(StandardCharsets.UTF_8));

        StringBuilder sb = new StringBuilder();
        sb.append("id,tick,vx,vy,vz,h,prevX,prevY,prevZ,prevH,victimSprint,victimGround,attacker,sprintState,attackerKb,distance,ux,uz\n");
        for (KBSample k : samples) {
            sb.append(k.id).append(',').append(k.tick).append(',')
              .append(KBProfile.f(k.vx, 5)).append(',').append(KBProfile.f(k.vy, 5)).append(',')
              .append(KBProfile.f(k.vz, 5)).append(',').append(KBProfile.f(k.h, 5)).append(',')
              .append(KBProfile.f(k.px, 5)).append(',').append(KBProfile.f(k.py, 5)).append(',')
              .append(KBProfile.f(k.pz, 5)).append(',').append(KBProfile.f(k.pH, 5)).append(',')
              .append(k.victimSprint).append(',').append(k.victimGround).append(',')
              .append(k.attacker.replace(',', '_')).append(',').append(k.sprintState).append(',')
              .append(k.attackerKb).append(',').append(KBProfile.f(k.distance, 3)).append(',')
              .append(KBProfile.f(k.ux, 4)).append(',').append(KBProfile.f(k.uz, 4)).append('\n');
        }
        File csv = new File(dir, "knockback-" + ts + "-samples.csv");
        Files.write(csv.toPath(), sb.toString().getBytes(StandardCharsets.UTF_8));
        return yml;
    }
}
"""

# ==============================================================================
# 3. KBProfile.java  (ORIGINAL)
# ==============================================================================
kb_profile = r"""package com.oryvex.kbclient.kb;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Carbon/Spigot knockback configuration with per-key confidence and source. */
public final class KBProfile {
    public static final int I_OPS = 0, I_H = 1, I_V = 2, I_EH = 3, I_EV = 4, I_F = 5,
            I_YL = 6, I_DTO = 7, I_DTV = 8, I_DYN = 9, I_LIMH = 10, I_HL = 11, COUNT = 12;
    public static final int SRC_NONE = 0, SRC_EST = 1, SRC_MEAS = 2, SRC_IMP = 3;
    public static final String[] SRC_TAG = { "DEF", "EST", "MEAS", "FILE" };

    /** flattened YAML paths, in file order */
    public static final String[] KEYS = {
            "ONE-POINT-SEVEN", "HORIZONTAL", "VERTICAL", "EXTRA-HORIZONTAL", "EXTRA-VERTICAL",
            "FRICTION", "Y-LIMIT", "DAMAGE-TICKS.OVERRIDE", "DAMAGE-TICKS.VALUE",
            "DYNAMIC-LIMIT", "LIMIT-HORIZONTAL", "H-LIMIT"
    };

    public boolean onePointSeven = false;
    public double horizontal = 0.4;
    public double vertical = 0.4;
    public double extraHorizontal = 0.5;
    public double extraVertical = 0.0;
    public double friction = 2.0;
    public double yLimit = 0.4;
    public boolean damageTicksOverride = false;
    public int damageTicksValue = 20;
    public boolean dynamicLimit = false;
    public boolean limitHorizontal = false;
    public double hLimit = 0.45;

    public final double[] conf = new double[COUNT];
    public final int[] src = new int[COUNT];
    public int total, used, walk, sprint, ambiguous;
    public boolean hasData, frictionMeasured;
    public double hSpread, vSpread;
    public final List<String> notes = new ArrayList<String>();

    public void mark(int i, double c) {
        conf[i] = c;
        src[i] = c >= 0.6 ? SRC_MEAS : (c > 0.0 ? SRC_EST : SRC_NONE);
    }

    public static String f(double v, int decimals) {
        return String.format(Locale.ROOT, "%." + decimals + "f", v);
    }

    public static String num(double v) {
        if (Double.isNaN(v) || Double.isInfinite(v)) return "0.0";
        String s = new BigDecimal(Double.toString(v)).toPlainString();
        if (s.indexOf('.') < 0) s += ".0";
        return s;
    }

    public static boolean isBool(int i) {
        return i == I_OPS || i == I_DTO || i == I_DYN || i == I_LIMH;
    }

    public String valueText(int i) {
        switch (i) {
            case I_OPS: return String.valueOf(onePointSeven);
            case I_H: return num(horizontal);
            case I_V: return num(vertical);
            case I_EH: return num(extraHorizontal);
            case I_EV: return num(extraVertical);
            case I_F: return num(friction);
            case I_YL: return num(yLimit);
            case I_DTO: return String.valueOf(damageTicksOverride);
            case I_DTV: return String.valueOf(damageTicksValue);
            case I_DYN: return String.valueOf(dynamicLimit);
            case I_LIMH: return String.valueOf(limitHorizontal);
            default: return num(hLimit);
        }
    }

    public double numeric(int i) {
        switch (i) {
            case I_OPS: return onePointSeven ? 1 : 0;
            case I_H: return horizontal;
            case I_V: return vertical;
            case I_EH: return extraHorizontal;
            case I_EV: return extraVertical;
            case I_F: return friction;
            case I_YL: return yLimit;
            case I_DTO: return damageTicksOverride ? 1 : 0;
            case I_DTV: return damageTicksValue;
            case I_DYN: return dynamicLimit ? 1 : 0;
            case I_LIMH: return limitHorizontal ? 1 : 0;
            default: return hLimit;
        }
    }

    public int compare(KBProfile ref, int i) {
        if (ref == null || ref.src[i] == SRC_NONE) return -1;
        double d = Math.abs(numeric(i) - ref.numeric(i));
        if (isBool(i) || i == I_DTV) return d == 0 ? 0 : 2;
        if (d <= 0.00051) return 0;
        return d <= 0.02 ? 1 : 2;
    }

    public static boolean parseBool(String v) {
        String s = v.trim().toLowerCase(Locale.ROOT);
        if (s.equals("true") || s.equals("yes") || s.equals("on")) return true;
        if (s.equals("false") || s.equals("no") || s.equals("off")) return false;
        throw new NumberFormatException(v);
    }

    public static double parseD(String v) {
        String s = v.trim();
        if (s.indexOf(',') >= 0 && s.indexOf('.') < 0) s = s.replace(',', '.');
        double d = Double.parseDouble(s);
        if (Double.isNaN(d) || Double.isInfinite(d)) throw new NumberFormatException(v);
        return d;
    }

    public static int parseI(String v) {
        String s = v.trim();
        try { return Integer.parseInt(s); } catch (NumberFormatException e) {
            double d = parseD(s);
            if (d != Math.rint(d)) throw new NumberFormatException(v);
            return (int) d;
        }
    }

    public void setFromText(int i, String v) {
        switch (i) {
            case I_OPS: onePointSeven = parseBool(v); break;
            case I_H: horizontal = parseD(v); break;
            case I_V: vertical = parseD(v); break;
            case I_EH: extraHorizontal = parseD(v); break;
            case I_EV: extraVertical = parseD(v); break;
            case I_F: friction = parseD(v); break;
            case I_YL: yLimit = parseD(v); break;
            case I_DTO: damageTicksOverride = parseBool(v); break;
            case I_DTV: damageTicksValue = parseI(v); break;
            case I_DYN: dynamicLimit = parseBool(v); break;
            case I_LIMH: limitHorizontal = parseBool(v); break;
            default: hLimit = parseD(v); break;
        }
        conf[i] = 1.0;
        src[i] = SRC_IMP;
    }

    public String summary() {
        return "H " + num(horizontal) + "  V " + num(vertical) + "  F " + num(friction);
    }

    public String toYaml() {
        StringBuilder sb = new StringBuilder();
        sb.append("ONE-POINT-SEVEN: ").append(onePointSeven).append("\n");
        sb.append("HORIZONTAL: ").append(num(horizontal)).append("\n");
        sb.append("VERTICAL: ").append(num(vertical)).append("\n");
        sb.append("EXTRA-HORIZONTAL: ").append(num(extraHorizontal)).append("\n");
        sb.append("EXTRA-VERTICAL: ").append(num(extraVertical)).append("\n");
        sb.append("FRICTION: ").append(num(friction)).append("\n");
        sb.append("Y-LIMIT: ").append(num(yLimit)).append("\n");
        sb.append("DAMAGE-TICKS:\n");
        sb.append("  OVERRIDE: ").append(damageTicksOverride).append("\n");
        sb.append("  VALUE: ").append(damageTicksValue).append("\n");
        sb.append("DYNAMIC-LIMIT: ").append(dynamicLimit).append("\n");
        sb.append("LIMIT-HORIZONTAL: ").append(limitHorizontal).append("\n");
        sb.append("H-LIMIT: ").append(num(hLimit));
        return sb.toString();
    }
}
"""

# ==============================================================================
# 4. KBSample.java  (ORIGINAL)
# ==============================================================================
kb_sample = r"""package com.oryvex.kbclient.kb;

public final class KBSample {
    public static final int WALK = 0, SPRINT = 1, AMBIGUOUS = 2;
    public final int id;
    public final long tick;
    public final double vx, vy, vz, h;
    public final double px, py, pz, pH;
    public final boolean victimSprint, victimGround;
    public final boolean hasAttacker;
    public final int sprintState;
    public final boolean attackerSprint;
    public final int attackerKb;
    public final double ux, uz;
    public final double distance;
    public final String attacker;

    public KBSample(int id, long tick, double vx, double vy, double vz,
                    double px, double py, double pz,
                    boolean victimSprint, boolean victimGround,
                    boolean hasAttacker, int sprintState, int attackerKb,
                    double ux, double uz, double distance, String attacker) {
        this.id = id;
        this.tick = tick;
        this.vx = vx; this.vy = vy; this.vz = vz;
        this.h = Math.sqrt(vx * vx + vz * vz);
        this.px = px; this.py = py; this.pz = pz;
        this.pH = Math.sqrt(px * px + pz * pz);
        this.victimSprint = victimSprint;
        this.victimGround = victimGround;
        this.hasAttacker = hasAttacker;
        this.sprintState = sprintState;
        this.attackerSprint = sprintState == SPRINT;
        this.attackerKb = attackerKb;
        this.ux = ux; this.uz = uz;
        this.distance = distance;
        this.attacker = attacker == null ? "?" : attacker;
    }
}
"""

# ==============================================================================
# EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("🔄 Restoring KB files to original defaults...\n")
    write_file(os.path.join(kb_pkg, "KBEstimator.java"), kb_estimator)
    write_file(os.path.join(root_pkg, "KBTracker.java"), kb_tracker)
    write_file(os.path.join(kb_pkg, "KBProfile.java"), kb_profile)
    write_file(os.path.join(kb_pkg, "KBSample.java"), kb_sample)
    print("\n✅ All KB files restored to their original versions.")
    print("   - KBEstimator: coarse+fine grid, plateau detection, solve(), capped groups")
    print("   - KBTracker:   MAX_SAMPLES=120, score-based attacker, CSV export")
    print("   - KBProfile:   original 12-key structure with conf/src tracking")
    print("   - KBSample:    original data class")