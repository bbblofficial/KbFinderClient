import os

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write_file(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated: {os.path.basename(path)}")

base_dir = os.path.dirname(os.path.abspath(__file__))
root_pkg = os.path.join(base_dir, "src", "main", "java", "com", "oryvex", "kbclient")
kb_pkg = os.path.join(root_pkg, "kb")

# ==============================================================================
# 1. KBEstimator.java (The Brain - Hyper-Accurate Math)
# ==============================================================================
kb_estimator_content = """package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Hyper-Accurate Solver for Carbon / Spigot knockback model.
 * Uses Variance Minimization for Friction and Trimmed Means for KB values.
 */
public final class KBEstimator {
    private KBEstimator() {}

    private static double r4(double v) { return Math.round(v * 10000.0) / 10000.0; }
    private static double r3(double v) { return Math.round(v * 1000.0) / 1000.0; }

    private static double median(List<Double> v) {
        if (v.isEmpty()) return 0;
        List<Double> c = new ArrayList<>(v);
        Collections.sort(c);
        int n = c.size();
        return (n % 2 == 1) ? c.get(n / 2) : (c.get(n / 2 - 1) + c.get(n / 2)) / 2.0;
    }

    // Trimmed mean ignores extreme outliers (e.g., packet spikes, critical hits)
    private static double trimmedMean(List<Double> v, double trimPct) {
        if (v.isEmpty()) return 0;
        List<Double> c = new ArrayList<>(v);
        Collections.sort(c);
        int n = c.size();
        int trim = (int) Math.floor(n * trimPct);
        if (trim == 0 || n - 2 * trim <= 0) return median(v);
        double sum = 0;
        for (int i = trim; i < n - trim; i++) sum += c.get(i);
        return sum / (n - 2 * trim);
    }

    private static double variance(List<Double> v, double mean) {
        if (v.size() < 2) return 0;
        double sumSq = 0;
        for (double d : v) sumSq += (d - mean) * (d - mean);
        return sumSq / v.size();
    }

    public static KBProfile calculate(List<KBSample> all) {
        KBProfile p = new KBProfile();
        p.total = (all == null) ? 0 : all.size();
        if (all == null || all.isEmpty()) {
            p.notes.add("Waiting for knockback...");
            return p;
        }

        // 1. STRICT FILTERING (Only ground, clean, non-enchanted hits)
        List<KBSample> clean = new ArrayList<>();
        int ignoredEnch = 0, ignoredAmb = 0, ignoredAir = 0;
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (k.attackerKb > 0) { ignoredEnch++; continue; } // Enchantments change the formula
            if (k.sprintState == KBSample.AMBIGUOUS) { ignoredAmb++; continue; } // W-taps
            if (!k.victimGround) { ignoredAir++; continue; } // Air KB has different dynamics
            if (k.h < 0.005 && Math.abs(k.vy) < 0.005) continue; // Network noise
            if (k.h > 4.0 || Math.abs(k.vy) > 4.0) continue; // Explosions / extreme outliers
            clean.add(k);
        }

        p.used = clean.size();
        p.ambiguous = ignoredAmb;
        if (ignoredEnch > 0) p.notes.add("Ignored " + ignoredEnch + " enchanted hits.");
        if (ignoredAir > 0) p.notes.add("Ignored " + ignoredAir + " mid-air hits (ground hits required for base accuracy).");
        if (ignoredAmb > 0) p.notes.add("Ignored " + ignoredAmb + " ambiguous sprint states.");

        detectDamageTicks(all, p);

        if (clean.size() < 3) {
            p.notes.add("Need at least 3 clean ground hits to calculate profile.");
            return p;
        }

        p.hasData = true;
        for (KBSample k : clean) { if (k.attackerSprint) p.sprint++; else p.walk++; }

        // 2. FRICTION ESTIMATION (Grid Search with Variance Minimization)
        double bestF = 2.0;
        double minVar = Double.MAX_VALUE;
        
        List<KBSample> walkHits = new ArrayList<>();
        for (KBSample k : clean) if (!k.attackerSprint) walkHits.add(k);
        
        if (walkHits.size() >= 2) {
            // Search friction from 1.0 to 3.0 with 0.001 precision
            for (double f = 1.0; f <= 3.0; f += 0.001) {
                double invF = 1.0 / f;
                List<Double> kbVals = new ArrayList<>();
                for (KBSample k : walkHits) {
                    double vOldAlong = k.px * k.ux + k.pz * k.uz;
                    double vNewAlong = k.vx * k.ux + k.vz * k.uz;
                    double kb = vNewAlong - (vOldAlong * invF);
                    if (kb > 0) kbVals.add(kb);
                }
                if (kbVals.size() >= 2) {
                    double med = median(kbVals);
                    double var = variance(kbVals, med);
                    if (var < minVar) {
                        minVar = var;
                        bestF = f;
                    }
                }
            }
        }
        
        p.friction = r3(bestF);
        p.frictionMeasured = walkHits.size() >= 2;
        p.mark(KBProfile.I_F, p.frictionMeasured ? 0.95 : 0.2);
        if (!p.frictionMeasured) p.notes.add("Friction defaulted to 2.0. Need more walk hits.");

        double invF = 1.0 / p.friction;

        // 3. CALCULATE KB VALUES (Horizontal & Vertical)
        List<Double> hWalk = new ArrayList<>(), hSprint = new ArrayList<>();
        List<Double> vWalk = new ArrayList<>(), vSprint = new ArrayList<>();

        for (KBSample k : clean) {
            double vOldH = k.px * k.ux + k.pz * k.uz;
            double vNewH = k.vx * k.ux + k.vz * k.uz;
            double kbH = vNewH - (vOldH * invF);
            
            double kbV = k.vy - (k.py * invF);

            if (k.attackerSprint) {
                if (kbH > 0) hSprint.add(kbH);
                if (kbV > 0) vSprint.add(kbV);
            } else {
                if (kbH > 0) hWalk.add(kbH);
                if (kbV > 0) vWalk.add(kbV);
            }
        }

        // Use trimmed mean (10% cut) to ignore extreme outliers
        double baseH = trimmedMean(hWalk, 0.1);
        double baseV = trimmedMean(vWalk, 0.1);
        
        double totalH = trimmedMean(hSprint, 0.1);
        double totalV = trimmedMean(vSprint, 0.1);

        p.horizontal = r4(baseH);
        p.vertical = r4(baseV);
        
        p.extraHorizontal = r4(Math.max(0, totalH - baseH));
        p.extraVertical = r4(Math.max(0, totalV - baseV));

        p.mark(KBProfile.I_H, hWalk.size() >= 2 ? 0.9 : 0.3);
        p.mark(KBProfile.I_V, vWalk.size() >= 2 ? 0.9 : 0.3);
        p.mark(KBProfile.I_EH, hSprint.size() >= 2 ? 0.9 : 0.3);
        p.mark(KBProfile.I_EV, vSprint.size() >= 2 ? 0.9 : 0.3);

        if (p.walk == 0) p.notes.add("Need NON-sprinting hits for accurate HORIZONTAL/VERTICAL.");
        if (p.sprint == 0) p.notes.add("Need SPRINTING hits for EXTRA-HORIZONTAL/VERTICAL.");

        // 4. LIMITS DETECTION
        double maxY = 0;
        for (KBSample k : clean) maxY = Math.max(maxY, k.vy);
        p.yLimit = r4(maxY);
        p.mark(KBProfile.I_YL, clean.size() >= 5 ? 0.8 : 0.4);

        double maxH = 0;
        for (KBSample k : clean) maxH = Math.max(maxH, k.h);
        p.hLimit = r4(maxH);
        p.limitHorizontal = maxH > 0.4 && maxH < 1.0; 
        p.mark(KBProfile.I_HL, 0.6);
        p.mark(KBProfile.I_LIMH, p.limitHorizontal ? 0.7 : 0.3);

        // 5. DYNAMIC LIMIT & 1.7
        p.dynamicLimit = false; 
        p.mark(KBProfile.I_DYN, 0.2);
        
        p.onePointSeven = (p.extraHorizontal < 0.01 && p.extraVertical < 0.01);
        p.mark(KBProfile.I_OPS, (p.walk > 0 && p.sprint > 0) ? 0.85 : 0.2);

        return p;
    }

    private static void detectDamageTicks(List<KBSample> all, KBProfile p) {
        List<Integer> gaps = new ArrayList<>();
        KBSample prev = null;
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (prev != null && prev.attacker.equals(k.attacker)) {
                long gap = k.tick - prev.tick;
                if (gap > 0 && gap < 40) gaps.add((int) gap);
            }
            prev = k;
        }

        p.damageTicksValue = 20;
        p.damageTicksOverride = false;

        if (gaps.isEmpty()) {
            p.mark(KBProfile.I_DTO, 0);
            p.mark(KBProfile.I_DTV, 0);
            p.notes.add("DAMAGE-TICKS unknown. Have someone hit you rapidly.");
            return;
        }

        Collections.sort(gaps);
        int minGap = gaps.get(0);
        
        if (minGap >= 10) {
            p.mark(KBProfile.I_DTO, 0.6);
            p.mark(KBProfile.I_DTV, 0.1);
            p.notes.add("Hit gap " + minGap + " ticks. OVERRIDE is likely false (vanilla 20).");
        } else {
            p.damageTicksValue = Math.max(2, minGap * 2);
            p.damageTicksOverride = true;
            p.mark(KBProfile.I_DTO, 0.9);
            p.mark(KBProfile.I_DTV, 0.85);
            p.notes.add("Shortest gap " + minGap + " ticks -> DAMAGE-TICKS.VALUE is " + p.damageTicksValue + ".");
        }
    }
}
"""

# ==============================================================================
# 2. KBTracker.java (Data Collection - Strict & Clean)
# ==============================================================================
kb_tracker_content = """package com.oryvex.kbclient;

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

public class KBTracker {
    public static final int MAX_SAMPLES = 200; // Increased buffer for better statistical accuracy
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
        chat(Theme.S + "b[KB] " + Theme.S + "7Recording " + Theme.S + "e" + goal + Theme.S + "7 hits.");
    }

    public synchronized KBYaml.Result importYaml(String text) {
        KBYaml.Result r = KBYaml.parse(text);
        if (r.parsed > 0) {
            reference = r.profile;
            lastImport = r.summary();
            chat(Theme.S + "a[KB] Imported: " + Theme.S + "f" + r.summary());
        } else {
            lastImport = "nothing imported";
            chat(Theme.S + "c[KB] No knockback keys found.");
        }
        return r;
    }

    public synchronized void clearReference() {
        reference = null;
        lastImport = "";
    }

    public synchronized void capture(int rawX, int rawY, int rawZ) {
        Minecraft mc = Minecraft.getMinecraft();
        EntityPlayerSP me = mc.thePlayer;
        if (!recording || me == null || mc.theWorld == null) return;

        double vx = rawX / 8000.0, vy = rawY / 8000.0, vz = rawZ / 8000.0;
        double h = Math.sqrt(vx * vx + vz * vz);
        
        if (h < 0.001 && Math.abs(vy) < 0.001) return; // Ignore micro-noise

        EntityPlayer attacker = null;
        double bestScore = -1.0e9;
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            if (e == me || e.isDead) continue;
            double dist = me.getDistanceToEntity(e);
            if (dist > 6.0) continue; // Strict range for accuracy
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

        // Capture exact pre-hit motion
        KBSample s = new KBSample(nextId++, tick, vx, vy, vz,
                me.motionX, me.motionY, me.motionZ, me.isSprinting(), me.onGround,
                has, state, kb, ux, uz, dist, name);
                
        samples.add(s);
        while (samples.size() > MAX_SAMPLES) samples.remove(0);
        last = s;
        
        profile = KBEstimator.calculate(samples);

        String tag = !has ? "no attacker" : (state == KBSample.AMBIGUOUS ? "W-TAP?" : (state == KBSample.SPRINT ? "SPRINT" : "WALK"));
        int col = !has ? Theme.DIM : (state == KBSample.AMBIGUOUS ? Theme.DIM : (state == KBSample.SPRINT ? Theme.WARN : Theme.GOOD));
        Hud.push("Hit #" + s.id + "  H:" + KBProfile.f(h, 4) + "  V:" + KBProfile.f(vy, 4) + "  [" + tag + "]", col);

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
    }

    public synchronized File export() throws IOException {
        File dir = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("Cannot create " + dir);
        String ts = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        File yml = new File(dir, "knockback-" + ts + ".yml");
        Files.write(yml.toPath(), (profile.toYaml() + "\\n").getBytes(StandardCharsets.UTF_8));
        return yml;
    }
}
"""

# ==============================================================================
# 3. KBProfile.java & KBSample.java (Keep structure intact but ensure precision)
# ==============================================================================
kb_profile_content = """package com.oryvex.kbclient.kb;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class KBProfile {
    public static final int I_OPS = 0, I_H = 1, I_V = 2, I_EH = 3, I_EV = 4, I_F = 5,
            I_YL = 6, I_DTO = 7, I_DTV = 8, I_DYN = 9, I_LIMH = 10, I_HL = 11, COUNT = 12;
    public static final int SRC_NONE = 0, SRC_EST = 1, SRC_MEAS = 2, SRC_IMP = 3;
    public static final String[] SRC_TAG = { "DEF", "EST", "MEAS", "FILE" };

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
        try { return Integer.parseInt(s); } 
        catch (NumberFormatException e) {
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
        sb.append("ONE-POINT-SEVEN: ").append(onePointSeven).append("\\n");
        sb.append("HORIZONTAL: ").append(num(horizontal)).append("\\n");
        sb.append("VERTICAL: ").append(num(vertical)).append("\\n");
        sb.append("EXTRA-HORIZONTAL: ").append(num(extraHorizontal)).append("\\n");
        sb.append("EXTRA-VERTICAL: ").append(num(extraVertical)).append("\\n");
        sb.append("FRICTION: ").append(num(friction)).append("\\n");
        sb.append("Y-LIMIT: ").append(num(yLimit)).append("\\n");
        sb.append("DAMAGE-TICKS:\\n");
        sb.append("  OVERRIDE: ").append(damageTicksOverride).append("\\n");
        sb.append("  VALUE: ").append(damageTicksValue).append("\\n");
        sb.append("DYNAMIC-LIMIT: ").append(dynamicLimit).append("\\n");
        sb.append("LIMIT-HORIZONTAL: ").append(limitHorizontal).append("\\n");
        sb.append("H-LIMIT: ").append(num(hLimit));
        return sb.toString();
    }
}
"""

kb_sample_content = """package com.oryvex.kbclient.kb;

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
    print("🚀 Applying Hyper-Accurate KB Extraction Logic...")
    write_file(os.path.join(kb_pkg, "KBEstimator.java"), kb_estimator_content)
    write_file(os.path.join(root_pkg, "KBTracker.java"), kb_tracker_content)
    write_file(os.path.join(kb_pkg, "KBProfile.java"), kb_profile_content)
    write_file(os.path.join(kb_pkg, "KBSample.java"), kb_sample_content)
    print("✨ Done! The KB Extractor is now extremely precise.")