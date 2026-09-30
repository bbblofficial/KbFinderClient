package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Solver for the Carbon / Spigot knockback model.
 *
 *   horizontal:  v_new = v_old / FRICTION + dir * (HORIZONTAL [+ EXTRA-HORIZONTAL if attacker sprints])
 *   vertical:    y_new = y_old / FRICTION + VERTICAL   [+ EXTRA-VERTICAL if attacker sprints]
 *                then clamped to Y-LIMIT
 *
 * Steps: (A) grid-search FRICTION by minimising the within-group variance of the
 * residual, (B) detect clamped plateaus (limits), (C) medians per group give the
 * base / extra values, (D) hit-gap analysis gives DAMAGE-TICKS.
 */
public final class KBEstimator {
    private KBEstimator() {}

    private static double conf(double n) { return 1.0 - Math.exp(-n / 3.0); }

    private static double median(List<Double> v) {
        if (v.isEmpty()) return 0;
        List<Double> c = new ArrayList<Double>(v);
        Collections.sort(c);
        int n = c.size();
        return (n % 2 == 1) ? c.get(n / 2) : (c.get(n / 2 - 1) + c.get(n / 2)) / 2.0;
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

    /** residual variance for a candidate friction value */
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
            if (!s.isEmpty()) { extra = median(s) - base; cE = conf(Math.min(w.size(), s.size())); }
            else if (!sC.isEmpty()) { extra = median(sC) - base; cE = 0.25; lb = 1; }
            else { extra = defExtra; cE = 0; }
        } else if (!s.isEmpty()) {
            extra = defExtra; base = median(s) - extra; cB = 0.25; cE = 0; spr = std(s);
        } else if (!wC.isEmpty() || !sC.isEmpty()) {
            List<Double> any = new ArrayList<Double>(wC);
            any.addAll(sC);
            extra = defExtra; base = median(any) - (wC.isEmpty() ? extra : 0); cB = 0.2; cE = 0; lb = 1;
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

        // ---- usable samples: a nearby attacker, no Knockback enchant, non-empty packet
        int ench = 0;
        List<KBSample> s = new ArrayList<KBSample>();
        for (KBSample k : all) {
            if (!k.hasAttacker) continue;
            if (k.attackerKb > 0) { ench++; continue; }
            if (k.h < 0.0005 && Math.abs(k.vy) < 0.0005) continue;
            s.add(k);
        }
        int n = s.size();
        p.used = n;
        if (ench > 0) p.notes.add("Ignored " + ench + " hit(s) from Knockback-enchanted weapons.");
        detectDamageTicks(all, p);
        if (n == 0) {
            p.notes.add("No usable hits yet (need a nearby attacking player).");
            return p;
        }
        p.hasData = true;
        for (KBSample k : s) { if (k.attackerSprint) p.sprint++; else p.walk++; }

        // ---- plateau detection (limits clamp many hits to the same value)
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
            for (double f = 1.0; f <= 6.0001; f += 0.01) {
                double c = cost(fit, f);
                if (c < best - 1e-12) { best = c; bestF = f; }
            }
            double c2 = cost(fit, 2.0);
            if (best < c2 * 0.6 && c2 - best > 1e-5) {
                F = bestF;
                p.frictionMeasured = true;
                p.cF = conf(moving / 2.0);
                if (F <= 1.03 || F >= 5.97) { p.cF *= 0.4; p.notes.add("FRICTION hit the search boundary - result is unreliable."); }
            } else {
                p.cF = 0.35;
                p.notes.add("FRICTION matches the default 2.000 (no evidence of another value).");
            }
        } else {
            p.cF = 0;
            p.notes.add("FRICTION defaulted to 2.000 - get hit while walking/strafing to measure it.");
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
        p.horizontal = hr[0]; p.extraHorizontal = hr[1]; p.cH = hr[2]; p.cEH = hr[3]; p.hSpread = hr[4];
        if (hr[5] > 0) p.notes.add("EXTRA-HORIZONTAL is only a lower bound (hits were clamped by H-LIMIT).");

        double[] vr = solve(vw, vs, vwC, vsC, 0.0);
        p.vertical = vr[0]; p.extraVertical = vr[1]; p.cV = vr[2]; p.cEV = vr[3]; p.vSpread = vr[4];
        if (vr[5] > 0) p.notes.add("EXTRA-VERTICAL is only a lower bound (hits were clamped by Y-LIMIT).");

        if (p.walk == 0) p.notes.add("Need hits from a NON-sprinting attacker to separate HORIZONTAL from EXTRA-HORIZONTAL.");
        if (p.sprint == 0) p.notes.add("Need hits from a SPRINTING attacker to measure the EXTRA-* values.");

        // ---- limits
        p.yLimit = yMax;
        if (yCapped) { p.cYL = conf(yPlN / 1.5); }
        else {
            p.cYL = 0.25;
            if (yMulti) p.notes.add("Y-LIMIT not confirmed - get hit in mid-air at different heights.");
        }
        p.hLimit = hMax;
        p.limitHorizontal = hCapped;
        p.cHL = hCapped ? conf(hPlN / 1.5) : 0.2;
        p.cLimH = hCapped ? conf(hPlN / 1.5) : (moving >= 3 ? 0.55 : 0.15);

        // ---- DYNAMIC-LIMIT (vertical zeroed when already above the limit)
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
        p.cDyn = dyn ? 0.6 : (airHigh >= 2 ? 0.5 : 0.12);

        // ---- ONE-POINT-SEVEN (heuristic: no sprint bonus at all)
        if (p.walk > 0 && p.sprint > 0) {
            boolean flat = p.extraHorizontal < 0.02 && p.extraVertical < 0.02;
            p.onePointSeven = flat;
            p.cOps = 0.35;
        } else {
            p.onePointSeven = false;
            p.cOps = 0.08;
        }
        return p;
    }

    /** DAMAGE-TICKS: a hit can land again once hurtTime <= max/2, so VALUE ~= 2 * shortest hit gap. */
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
        if (iv.isEmpty()) {
            p.damageTicksValue = 20;
            p.damageTicksOverride = false;
            p.cDT = 0;
            p.notes.add("DAMAGE-TICKS unknown - have someone hit you rapidly.");
            return;
        }
        Collections.sort(iv);
        int m = iv.size() >= 4 ? iv.get(1) : iv.get(0);
        if (m >= 9) {
            p.damageTicksValue = 20;
            p.damageTicksOverride = false;
            p.cDT = iv.size() >= 3 ? 0.45 : 0.2;
            if (m >= 10 && iv.size() >= 3) p.notes.add("Shortest hit gap is " + m + " ticks - consistent with vanilla 20 damage ticks.");
        } else {
            p.damageTicksValue = Math.max(2, m * 2);
            p.damageTicksOverride = true;
            p.cDT = iv.size() >= 4 ? 0.75 : 0.45;
            p.notes.add("Shortest hit gap is " + m + " ticks -> DAMAGE-TICKS ~ " + (m * 2) + ".");
        }
    }
}
