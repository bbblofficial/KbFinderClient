#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adder.py - high-precision KB Extractor upgrade.

Replaces KBSample.java, KBTracker.java, KBEstimator.java.

Run from the project root (where build.gradle is):
    python adder.py
"""

import os, sys, hashlib, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src", "main", "java", "com", "oryvex", "kbclient")
KB   = os.path.join(SRC, "kb")


def sha1(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def check_balance(name, text):
    o, c = text.count("{"), text.count("}")
    if o != c:
        print(f"  !! {name}: {{={o}  }}={c}  NOT BALANCED")
        return False
    return True


def fresh_write(path, text):
    name = os.path.basename(path)
    if not check_balance(name, text):
        print("  ABORT: refusing to write unbalanced file", name); sys.exit(1)
    if os.path.isfile(path):
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        try: os.replace(path, path + ".old_" + stamp)
        except OSError: os.remove(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"  write {os.path.relpath(path, ROOT)}  sha1={sha1(text)}")


# =====================================================================
#  KBSample.java
# =====================================================================
KBSAMPLE = r'''package com.oryvex.kbclient.kb;

/**
 * One knockback event plus the extra context we now capture for accuracy.
 *
 *  attackerVx/Vz     - attacker's horizontal motion at hit time
 *  attackerLookDot   - how well the attacker's view aims at us [0..1]
 *  victimSpeed       - our pre-hit horizontal speed
 *  confidence        - composite 0..100 score for how trustworthy this sample is
 */
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

    /* --- accuracy additions --- */
    public final double attackerVx, attackerVz;
    public final double attackerLookDot;
    public final double victimSpeed;
    public final int confidence;

    public KBSample(int id, long tick,
                    double vx, double vy, double vz,
                    double px, double py, double pz,
                    boolean victimSprint, boolean victimGround,
                    boolean hasAttacker, int sprintState, int attackerKb,
                    double ux, double uz, double distance, String attacker,
                    double attackerVx, double attackerVz,
                    double attackerLookDot, double victimSpeed,
                    int confidence) {
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
        this.attackerVx = attackerVx;
        this.attackerVz = attackerVz;
        this.attackerLookDot = attackerLookDot;
        this.victimSpeed = victimSpeed;
        this.confidence = confidence;
    }
}
'''


# =====================================================================
#  KBTracker.java  (full rewrite, accuracy-focused)
# =====================================================================
KBTRACKER = r'''package com.oryvex.kbclient;

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
import net.minecraft.util.Vec3;

/**
 * Collects knockback samples (main thread only), keeps a live profile and an
 * imported reference.
 *
 * v2 accuracy upgrades:
 *   - attacker scored on 4 factors (distance / velocity-alignment / view / motion)
 *   - sprint history window widened 3 -> 5 ticks (0x1F)
 *   - per-sample confidence 0..100
 *   - victim's pre-hit horizontal speed recorded
 */
public class KBTracker {
    public static final int MAX_SAMPLES = 200;

    private final List<KBSample> samples = new ArrayList<KBSample>();
    private final Map<Integer, Integer> sprintBits = new HashMap<Integer, Integer>();
    private KBProfile profile = new KBProfile();
    private KBProfile reference;
    private String lastImport = "";
    private KBSample last;
    private boolean recording = false;
    private int goal = 0;
    private int sessionHits = 0;
    private int nextId = 1;
    private long tick = 0;
    private String server = "-";

    public KBTracker() {
        profile.notes.add("Waiting for knockback - get hit by another player.");
    }

    /** per client tick: remember the last 5 ticks of every player's sprint flag. */
    public synchronized void tick() {
        tick++;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.theWorld == null) return;
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            int id = e.getEntityId();
            int s = e.isSprinting() ? 1 : 0;
            Integer b = sprintBits.get(id);
            int nb = (b == null) ? (s == 1 ? 0x1F : 0) : (((b << 1) | s) & 0x1F);
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
        recording = false;
        goal = 0;
    }

    public synchronized void startGoal(int hits) {
        reset();
        goal = Math.max(1, hits);
        recording = true;
        chat(Theme.S + "b[KB] " + Theme.S + "7Recording " + Theme.S + "e" + goal
                + Theme.S + "7 hits. Get hit by sprinting AND walking players.");
    }

    /* ---- YAML reference ---- */
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
        double h  = Math.sqrt(vx * vx + vz * vz);

        /* ---------- attacker identification (4-factor score) ---------- */
        EntityPlayer attacker = null;
        double bestScore = 0.0;
        double bestAttVx = 0, bestAttVz = 0, bestLook = 0;

        for (EntityPlayer e : mc.theWorld.playerEntities) {
            if (e == me || e.isDead) continue;

            /* body-to-eye distance */
            double dx = me.posX - e.posX;
            double dz = me.posZ - e.posZ;
            double dy = (me.posY + me.getEyeHeight()) - (e.posY + e.getEyeHeight() * 0.5);
            double dist3d = Math.sqrt(dx * dx + dy * dy + dz * dz);
            if (dist3d > 5.0) continue;

            double dh = Math.sqrt(dx * dx + dz * dz);
            if (dh < 0.05) continue;
            double ux = dx / dh, uz = dz / dh;

            /* velocity must be along the away-from-attacker direction */
            double vDot = (h > 0.05) ? ((vx * ux + vz * uz) / h) : 0.0;
            if (vDot < 0.2) continue;

            /* attacker's view direction */
            double lookDot = 0.0;
            try {
                Vec3 look = e.getLookVec();
                double lx = -dx, ly = -dy, lz = -dz;
                double ln = Math.sqrt(lx * lx + ly * ly + lz * lz);
                if (ln > 0.01) {
                    lookDot = (look.xCoord * lx + look.yCoord * ly + look.zCoord * lz) / ln;
                    if (lookDot < 0) lookDot = 0;
                    if (lookDot > 1) lookDot = 1;
                }
            } catch (Throwable ignored) { }

            /* attacker's motion toward victim */
            double aSpeed = Math.sqrt(e.motionX * e.motionX + e.motionZ * e.motionZ);
            double aAlign = 0.0;
            if (aSpeed > 0.01) {
                aAlign = -(e.motionX * ux + e.motionZ * uz) / aSpeed;
                if (aAlign < 0) aAlign = 0;
                if (aAlign > 1) aAlign = 1;
            }

            double proximity = Math.max(0, 1 - dist3d / 5.0);
            double score = proximity * 0.35
                         + vDot      * 0.35
                         + lookDot   * 0.20
                         + aAlign    * 0.10;

            if (score > bestScore) {
                bestScore = score;
                attacker   = e;
                bestAttVx  = e.motionX;
                bestAttVz  = e.motionZ;
                bestLook   = lookDot;
            }
        }

        boolean has = attacker != null && bestScore >= 0.35;
        if (!has) attacker = null;

        double ux = 0, uz = 0, dist = 0;
        int state = KBSample.WALK;
        int kb = 0;
        String name = "?";
        double attVx = 0, attVz = 0, lookDot = 0;
        int confidence = 0;

        if (has) {
            double dx = me.posX - attacker.posX, dz = me.posZ - attacker.posZ;
            double dh = Math.sqrt(dx * dx + dz * dz);
            if (dh > 0.001) { ux = dx / dh; uz = dz / dh; }
            else if (h > 0.001) { ux = vx / h; uz = vz / h; }

            Integer bits = sprintBits.get(attacker.getEntityId());
            if (bits == null) {
                state = attacker.isSprinting() ? KBSample.SPRINT : KBSample.WALK;
            } else if (bits == 0x1F) {
                state = KBSample.SPRINT;
            } else if (bits == 0x00) {
                state = KBSample.WALK;
            } else {
                state = KBSample.AMBIGUOUS;
            }

            try { kb = EnchantmentHelper.getKnockbackModifier(attacker); }
            catch (Throwable ignored) { }

            name   = attacker.getName();
            dist   = me.getDistanceToEntity(attacker);
            attVx  = bestAttVx;
            attVz  = bestAttVz;
            lookDot = bestLook;

            double prox   = Math.max(0, 1 - dist / 5.0);
            double vAlign = (h > 0.01) ? Math.max(0, (vx * ux + vz * uz) / h) : 0;
            double sprintClarity = (state == KBSample.AMBIGUOUS) ? 0 : 1;
            confidence = (int) Math.round(
                    (prox * 0.30 + vAlign * 0.35 + lookDot * 0.20 + sprintClarity * 0.15) * 100);
        }

        double victimSpeed = Math.sqrt(me.motionX * me.motionX + me.motionZ * me.motionZ);

        KBSample s = new KBSample(
                nextId++, tick,
                vx, vy, vz,
                me.motionX, me.motionY, me.motionZ,
                me.isSprinting(), me.onGround,
                has, state, kb, ux, uz, dist, name,
                attVx, attVz, lookDot, victimSpeed, confidence);

        samples.add(s);
        while (samples.size() > MAX_SAMPLES) samples.remove(0);
        last = s;
        profile = KBEstimator.calculate(samples);

        String tag = !has ? "no attacker"
                : (state == KBSample.AMBIGUOUS ? "W-TAP?"
                : (state == KBSample.SPRINT ? "SPRINT" : "WALK"));
        int col = !has ? Theme.DIM
                : (state == KBSample.AMBIGUOUS ? Theme.DIM
                : (state == KBSample.SPRINT ? Theme.WARN : Theme.GOOD));
        Hud.push("Hit #" + s.id + "  H " + KBProfile.f(h, 4)
                + "  V " + KBProfile.f(vy, 4)
                + "  " + tag + "  [" + confidence + "%]", col);

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
        chat(g + "HORIZONTAL: " + w + p.valueText(KBProfile.I_H)
                + g + "   EXTRA-H: " + w + p.valueText(KBProfile.I_EH));
        chat(g + "VERTICAL: " + w + p.valueText(KBProfile.I_V)
                + g + "   EXTRA-V: " + w + p.valueText(KBProfile.I_EV));
        chat(g + "FRICTION: " + w + p.valueText(KBProfile.I_F)
                + g + "   Y-LIMIT: " + w + p.valueText(KBProfile.I_YL));
        chat(g + "DAMAGE-TICKS: " + w + p.damageTicksValue
                + g + " (override " + p.damageTicksOverride + ")");
        chat(Theme.S + "aOpen the analyzer with [Right Shift] or /kb");
    }

    public synchronized File export() throws IOException {
        File dir = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("Cannot create " + dir);
        String ts = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.ROOT).format(new Date());
        File yml = new File(dir, "knockback-" + ts + ".yml");
        Files.write(yml.toPath(), (profile.toYaml() + "\n").getBytes(StandardCharsets.UTF_8));

        StringBuilder sb = new StringBuilder();
        sb.append("id,tick,vx,vy,vz,h,prevX,prevY,prevZ,prevH,victimSprint,victimGround,")
          .append("attacker,sprintState,attackerKb,distance,ux,uz,")
          .append("attackerVx,attackerVz,attackerLookDot,victimSpeed,confidence\n");
        for (KBSample k : samples) {
            sb.append(k.id).append(',').append(k.tick).append(',')
              .append(KBProfile.f(k.vx, 5)).append(',').append(KBProfile.f(k.vy, 5)).append(',')
              .append(KBProfile.f(k.vz, 5)).append(',').append(KBProfile.f(k.h, 5)).append(',')
              .append(KBProfile.f(k.px, 5)).append(',').append(KBProfile.f(k.py, 5)).append(',')
              .append(KBProfile.f(k.pz, 5)).append(',').append(KBProfile.f(k.pH, 5)).append(',')
              .append(k.victimSprint).append(',').append(k.victimGround).append(',')
              .append(k.attacker.replace(',', '_')).append(',').append(k.sprintState).append(',')
              .append(k.attackerKb).append(',').append(KBProfile.f(k.distance, 3)).append(',')
              .append(KBProfile.f(k.ux, 4)).append(',').append(KBProfile.f(k.uz, 4)).append(',')
              .append(KBProfile.f(k.attackerVx, 5)).append(',').append(KBProfile.f(k.attackerVz, 5)).append(',')
              .append(KBProfile.f(k.attackerLookDot, 4)).append(',')
              .append(KBProfile.f(k.victimSpeed, 5)).append(',').append(k.confidence).append('\n');
        }
        File csv = new File(dir, "knockback-" + ts + "-samples.csv");
        Files.write(csv.toPath(), sb.toString().getBytes(StandardCharsets.UTF_8));
        return yml;
    }
}
'''


# =====================================================================
#  KBEstimator.java  (full rewrite)
# =====================================================================
KBESTIMATOR = r'''package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * High-precision solver for the Carbon / Spigot knockback model.
 *
 *   horizontal:  v_new = v_old / FRICTION + dir * (H + [EH if attacker sprints])
 *   vertical:    y_new = y_old / FRICTION + V   [+ EV if attacker sprints]
 *                (clamped to Y-LIMIT)
 *
 * Accuracy upgrades:
 *   - only samples with confidence >= 35 are used
 *   - FRICTION via golden-section search to ~1e-6 (was a 0.001 grid)
 *   - base values use a Gaussian KDE mode (was the median)
 *   - outlier rejection via MAD (median absolute deviation, k=3)
 *   - plateaus detected with a statistical spread test
 */
public final class KBEstimator {
    private KBEstimator() {}

    private static final int MIN_CONFIDENCE = 35;

    private static double conf(double n) { return 1.0 - Math.exp(-n / 3.0); }
    private static double r4(double v) { return Math.rint(v * 10000.0) / 10000.0; }

    /* ---------------- statistics ---------------- */
    static double median(List<Double> v) {
        if (v.isEmpty()) return 0;
        List<Double> c = new ArrayList<Double>(v);
        Collections.sort(c);
        int n = c.size();
        return (n % 2 == 1) ? c.get(n / 2) : (c.get(n / 2 - 1) + c.get(n / 2)) / 2.0;
    }

    static double mad(List<Double> v) {
        if (v.isEmpty()) return 0;
        double med = median(v);
        List<Double> devs = new ArrayList<Double>(v.size());
        for (double x : v) devs.add(Math.abs(x - med));
        return median(devs);
    }

    static double std(List<Double> v) {
        if (v.size() < 2) return 0;
        double m = 0;
        for (double d : v) m += d;
        m /= v.size();
        double s = 0;
        for (double d : v) s += (d - m) * (d - m);
        return Math.sqrt(s / (v.size() - 1));
    }

    static double max(List<Double> v) {
        double m = -Double.MAX_VALUE;
        for (double d : v) m = Math.max(m, d);
        return m;
    }

    static double spread(List<Double> v) {
        if (v.isEmpty()) return 0;
        double lo = Double.MAX_VALUE, hi = -Double.MAX_VALUE;
        for (double d : v) { lo = Math.min(lo, d); hi = Math.max(hi, d); }
        return hi - lo;
    }

    /** Gaussian KDE mode with Silverman's bandwidth. */
    static double kdeMode(List<Double> v) {
        if (v.isEmpty()) return 0;
        if (v.size() == 1) return v.get(0);
        double lo = Double.MAX_VALUE, hi = -Double.MAX_VALUE;
        for (double d : v) { lo = Math.min(lo, d); hi = Math.max(hi, d); }
        double range = hi - lo;
        if (range < 1e-9) return lo;
        double sd = std(v);
        double bw = 1.06 * sd * Math.pow(v.size(), -0.2);
        if (bw < 1e-6 || bw > range) bw = range / 20.0;
        double best = lo, bestDensity = -1;
        for (int i = 0; i <= 400; i++) {
            double t = lo + (hi - lo) * i / 400.0;
            double density = 0;
            for (double x : v) {
                double z = (t - x) / bw;
                density += Math.exp(-0.5 * z * z);
            }
            if (density > bestDensity) { bestDensity = density; best = t; }
        }
        return best;
    }

    /** keep values within k * 1.4826 * MAD of the median. */
    static List<Double> rejectOutliers(List<Double> v, double k) {
        if (v.size() < 5) return v;
        double med = median(v);
        double mad = mad(v);
        if (mad < 1e-9) return v;
        double threshold = k * 1.4826 * mad;
        List<Double> out = new ArrayList<Double>();
        for (double x : v) if (Math.abs(x - med) <= threshold) out.add(x);
        return out;
    }

    /* ---------------- friction cost ---------------- */
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

    /** golden-section minimisation to ~1e-6. */
    private static double bestFriction(List<KBSample> fit, double loF, double hiF) {
        double a = loF, b = hiF;
        final double gr = (Math.sqrt(5.0) - 1.0) / 2.0;
        double c = b - gr * (b - a);
        double d = a + gr * (b - a);
        double fc = cost(fit, c), fd = cost(fit, d);
        for (int i = 0; i < 90 && b - a > 1e-6; i++) {
            if (fc < fd) {
                b = d; d = c; fd = fc;
                c = b - gr * (b - a);
                fc = cost(fit, c);
            } else {
                a = c; c = d; fc = fd;
                d = a + gr * (b - a);
                fd = cost(fit, d);
            }
        }
        return (a + b) / 2.0;
    }

    /* ---------------- per-group solver ---------------- */
    /** returns {base, extra, confBase, confExtra, spread, lowerBoundFlag} */
    private static double[] solve(List<Double> w, List<Double> s,
                                  List<Double> wC, List<Double> sC, double defExtra) {
        w  = rejectOutliers(w,  3.0);
        s  = rejectOutliers(s,  3.0);
        wC = rejectOutliers(wC, 3.0);
        sC = rejectOutliers(sC, 3.0);

        double base, extra, cB, cE, spr = 0, lb = 0;
        if (!w.isEmpty()) {
            base = kdeMode(w);
            cB = conf(w.size());
            spr = std(w);
            if (!wC.isEmpty() && max(wC) > base) { base = max(wC); lb = 1; }
            if (!s.isEmpty()) {
                extra = kdeMode(s) - base;
                cE = conf(Math.min(w.size(), s.size()));
            } else if (!sC.isEmpty()) {
                extra = max(sC) - base; cE = 0.25; lb = 1;
            } else { extra = defExtra; cE = 0; }
        } else if (!s.isEmpty()) {
            extra = defExtra;
            base = kdeMode(s) - extra;
            cB = 0.25; cE = 0; spr = std(s);
        } else if (!wC.isEmpty() || !sC.isEmpty()) {
            extra = defExtra;
            base = !wC.isEmpty() ? max(wC) : max(sC) - extra;
            cB = 0.2; cE = 0; lb = 1;
        } else {
            base = 0; extra = defExtra; cB = 0; cE = 0;
        }
        return new double[] { Math.max(0, base), Math.max(0, extra), cB, cE, spr, lb };
    }

    /* ---------------- main entry ---------------- */
    public static KBProfile calculate(List<KBSample> all) {
        KBProfile p = new KBProfile();
        p.total = (all == null) ? 0 : all.size();
        if (all == null || all.isEmpty()) {
            p.notes.add("Waiting for knockback - get hit by another player.");
            return p;
        }

        int ench = 0, amb = 0, lowConf = 0;
        List<KBSample> s = new ArrayList<KBSample>();
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (k.confidence < MIN_CONFIDENCE) { lowConf++; continue; }
            if (k.sprintState == KBSample.AMBIGUOUS) { amb++; continue; }
            if (k.attackerKb > 0) { ench++; continue; }
            if (k.h < 0.0005 && Math.abs(k.vy) < 0.0005) continue;
            s.add(k);
        }
        int n = s.size();
        p.used = n;
        p.ambiguous = amb;
        if (ench > 0)    p.notes.add("Ignored " + ench + " hit(s) from Knockback-enchanted weapons.");
        if (amb > 0)     p.notes.add("Ignored " + amb + " hit(s) with an unclear attacker sprint state (W-tap).");
        if (lowConf > 0) p.notes.add("Ignored " + lowConf + " low-confidence hit(s) (far / misaimed / unknown attacker).");

        detectDamageTicks(all, p);

        if (n == 0) {
            p.notes.add("No usable hits yet - get hit by a player standing right next to you.");
            return p;
        }

        p.hasData = true;
        for (KBSample k : s) if (k.attackerSprint) p.sprint++; else p.walk++;

        /* ---- plateau detection ---- */
        double yMax = -10, hMax = 0;
        for (KBSample k : s) { yMax = Math.max(yMax, k.vy); hMax = Math.max(hMax, k.h); }
        boolean[] hPl = new boolean[n], yPl = new boolean[n];
        int hPlN = 0, yPlN = 0;
        for (int i = 0; i < n; i++) {
            KBSample k = s.get(i);
            if (k.h  >= hMax - 0.002) { hPl[i] = true; hPlN++; }
            if (k.vy >= yMax - 0.0015) { yPl[i] = true; yPlN++; }
        }
        boolean hMulti = hPlN >= 2 && hPlN < n;
        boolean yMulti = yPlN >= 2 && yPlN < n;

        /* ---- friction (golden-section) ---- */
        List<KBSample> fit = new ArrayList<KBSample>();
        for (int i = 0; i < n; i++) {
            if ((hMulti && hPl[i]) || (yMulti && yPl[i])) continue;
            fit.add(s.get(i));
        }
        if (fit.size() < 4) fit = s;

        int moving = 0;
        for (KBSample k : fit) if (k.pH > 0.06 || k.victimSpeed > 0.06) moving++;

        double F = 2.0;
        if (moving >= 4) {
            double f1 = bestFriction(fit, 1.0, 6.0);
            double c2 = cost(fit, 2.0);
            double cBest = cost(fit, f1);
            double cBoundary = Math.max(cost(fit, 1.5), cost(fit, 3.0));
            boolean informative = cBoundary - cBest > 1e-5;
            if (informative && Math.abs(f1 - 2.0) < 1e-4) {
                F = 2.0;
                p.frictionMeasured = true;
                p.mark(KBProfile.I_F, conf(moving / 2.0));
            } else if (cBest < c2 * 0.85 && c2 - cBest > 1e-5) {
                F = f1;
                p.frictionMeasured = true;
                double cf = conf(moving / 2.0);
                if (F <= 1.001 || F >= 5.999) {
                    cf *= 0.4;
                    p.notes.add("FRICTION hit a search boundary - result may be unreliable.");
                }
                p.mark(KBProfile.I_F, cf);
            } else {
                F = 2.0;
                p.mark(KBProfile.I_F, 0.35);
                p.notes.add("FRICTION matches the default 2.0 (no evidence of another value).");
            }
        } else {
            p.mark(KBProfile.I_F, 0);
            p.notes.add("FRICTION not measured - get hit while walking/strafing (pre-hit speed > 0.06).");
        }
        F = Math.round(F * 1000000.0) / 1000000.0;
        p.friction = F;

        /* ---- plateau cap check ---- */
        boolean hCapped = false, yCapped = false;
        if (hMulti) {
            List<Double> pa = new ArrayList<Double>();
            for (int i = 0; i < n; i++) if (hPl[i]) {
                KBSample k = s.get(i);
                pa.add((k.px * k.ux + k.pz * k.uz) / F);
            }
            hCapped = spread(pa) >= 0.03;
        }
        if (yMulti) {
            List<Double> pa = new ArrayList<Double>();
            for (int i = 0; i < n; i++) if (yPl[i]) pa.add(s.get(i).py / F);
            yCapped = spread(pa) >= 0.03;
        }

        /* ---- residual groups ---- */
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
            else                  { (hc ? hwC : hw).add(along); (yc ? vwC : vw).add(ry); }
        }

        double[] hr = solve(hw, hs, hwC, hsC, 0.5);
        p.horizontal = r4(hr[0]);
        p.extraHorizontal = r4(hr[1]);
        p.hSpread = hr[4];
        p.mark(KBProfile.I_H, hr[2]);
        p.mark(KBProfile.I_EH, hr[3]);
        if (hr[5] > 0) p.notes.add("HORIZONTAL/EXTRA-HORIZONTAL are lower bounds (H-LIMIT clamped them).");

        double[] vr = solve(vw, vs, vwC, vsC, 0.0);
        p.vertical = r4(vr[0]);
        p.extraVertical = r4(vr[1]);
        p.vSpread = vr[4];
        p.mark(KBProfile.I_V, vr[2]);
        p.mark(KBProfile.I_EV, vr[3]);
        if (vr[5] > 0) p.notes.add("VERTICAL is a lower bound (Y-LIMIT clamped it). Get hit while FALLING to unclamp.");

        if (p.walk == 0)   p.notes.add("Need hits from a NON-sprinting attacker to split HORIZONTAL from EXTRA-HORIZONTAL.");
        if (p.sprint == 0) p.notes.add("Need hits from a SPRINTING attacker to measure EXTRA-HORIZONTAL / EXTRA-VERTICAL.");

        /* ---- limits ---- */
        p.yLimit = r4(yMax);
        if (yCapped) {
            p.mark(KBProfile.I_YL, conf(yPlN / 1.5));
        } else {
            p.mark(KBProfile.I_YL, 0.25);
            p.notes.add("Y-LIMIT is only the highest vertical hit seen - get hit mid-air at different heights.");
        }
        p.hLimit = r4(hMax);
        p.limitHorizontal = hCapped;
        p.mark(KBProfile.I_LIMH, hCapped ? conf(hPlN / 1.5) : (moving >= 3 ? 0.55 : 0.15));
        p.mark(KBProfile.I_HL,  hCapped ? conf(hPlN / 1.5) : 0.15);
        if (!hCapped) p.notes.add("H-LIMIT looks inactive (never clamped). Value shown is just the largest horizontal hit.");

        /* ---- DYNAMIC-LIMIT ---- */
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

        /* ---- ONE-POINT-SEVEN ---- */
        if (p.walk > 0 && p.sprint > 0) {
            p.onePointSeven = p.extraHorizontal < 0.02 && p.extraVertical < 0.02;
            p.mark(KBProfile.I_OPS, 0.35);
        } else {
            p.onePointSeven = false;
            p.mark(KBProfile.I_OPS, 0.08);
        }
        return p;
    }

    /* ---- damage ticks ---- */
    private static void detectDamageTicks(List<KBSample> all, KBProfile p) {
        List<Integer> iv = new ArrayList<Integer>();
        KBSample prev = null;
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (k.confidence < MIN_CONFIDENCE) continue;
            if (prev != null && prev.attacker.equals(k.attacker)) {
                long d = k.tick - prev.tick;
                if (d >= 1 && d <= 40) iv.add((int) d);
            }
            prev = k;
        }
        p.damageTicksValue = 20;
        p.damageTicksOverride = false;
        if (iv.isEmpty()) {
            p.mark(KBProfile.I_DTO, 0);
            p.mark(KBProfile.I_DTV, 0);
            p.notes.add("DAMAGE-TICKS unknown - have someone click you rapidly.");
            return;
        }
        Collections.sort(iv);
        int m = iv.size() >= 4 ? iv.get(1) : iv.get(0);
        if (m >= 10) {
            p.mark(KBProfile.I_DTO, iv.size() >= 3 ? 0.45 : 0.2);
            p.mark(KBProfile.I_DTV, 0);
            p.notes.add("Shortest hit gap " + m + " ticks = vanilla 20. VALUE is not observable while OVERRIDE is false.");
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
'''


# =====================================================================
#  main
# =====================================================================
def main():
    print("== KB Client - high-precision Extractor upgrade ==")
    if not os.path.isdir(SRC):
        print("!! Run this from the project root (where build.gradle is).")
        sys.exit(1)

    print("\n[1/3] KBSample.java")
    fresh_write(os.path.join(KB, "KBSample.java"), KBSAMPLE)

    print("\n[2/3] KBTracker.java")
    fresh_write(os.path.join(SRC, "KBTracker.java"), KBTRACKER)

    print("\n[3/3] KBEstimator.java")
    fresh_write(os.path.join(KB, "KBEstimator.java"), KBESTIMATOR)

    print("\n== done ==")
    print()
    print(">>> commit and push <<<")
    print("    git add -A")
    print('    git commit -m "High-precision Extractor: 4-factor attacker ID, golden-section friction, KDE mode"')
    print("    git push")


if __name__ == "__main__":
    main()