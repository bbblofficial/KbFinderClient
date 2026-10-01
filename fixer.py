import os
import shutil

TARGET_FILE = os.path.join(
    "src", "main", "java", "com", "oryvex", "kbclient", "kb", "KBEstimator.java"
)

CLEAN_JAVA_CODE = '''package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Solver for the Carbon / Spigot knockback model.
 *
 *   horizontal:  v_new = v_old / FRICTION + dir * (HORIZONTAL [+ EXTRA-HORIZONTAL if attacker sprints])
 *   vertical:    y_new = y_old / FRICTION + VERTICAL   [+ EXTRA-VERTICAL if attacker sprints]  -> clamped to Y-LIMIT
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
        double base = 0, extra = defExtra, cB = 0, cE = 0, spr = 0, lb = 0;
        
        if (!w.isEmpty()) {
            base = median(w);
            cB = conf(w.size());
            spr = std(w);
            if (!wC.isEmpty() && max(wC) > base) { base = max(wC); lb = 1; }
            
            if (!s.isEmpty()) {
                extra = median(s) - base;
                cE = conf(Math.min(w.size(), s.size()));
            } else if (!sC.isEmpty()) {
                extra = max(sC) - base;
                cE = 0.25; lb = 1;
            }
        } else if (!s.isEmpty()) {
            double ms = median(s);
            if (ms >= defExtra) {
                base = ms - defExtra;
                extra = defExtra;
            } else {
                base = 0;
                extra = ms;
            }
            cB = 0.25; cE = 0; spr = std(s);
        } else if (!wC.isEmpty() || !sC.isEmpty()) {
            if (!wC.isEmpty()) {
                base = max(wC);
                extra = defExtra;
            } else {
                double ms = max(sC);
                if (ms >= defExtra) {
                    base = ms - defExtra;
                    extra = defExtra;
                } else {
                    base = 0;
                    extra = ms;
                }
            }
            cB = 0.2; cE = 0; lb = 1;
        }

        // Fix for negative base values dropping everything to 0.0
        if (base < 0) {
            extra += base;
            base = 0;
        }
        if (extra < 0) extra = 0;

        return new double[] { base, extra, cB, cE, spr, lb };
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
'''

def main():
    if not os.path.exists(TARGET_FILE):
        print(f"❌ Error: Cannot find {TARGET_FILE}")
        print("لطفاً مطمئن شوید دستور را در پوشه اصلی KnockbackClientMod اجرا می‌کنید.")
        return

    # ایجاد بکاپ از فایل فعلی
    backup_path = TARGET_FILE + ".bak"
    shutil.copy2(TARGET_FILE, backup_path)
    print(f"📦 بکاپ فایل قدیمی در {backup_path} ذخیره شد.")

    # بازنویسی مستقیم و استاندارد با UTF-8 و خطوط Unix LF
    with open(TARGET_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(CLEAN_JAVA_CODE)

    print("🎉 باگ با موفقیت برطرف شد! فایل KBEstimator.java کاملاً بازنویسی و پچ گردید.")

if __name__ == "__main__":
    main()