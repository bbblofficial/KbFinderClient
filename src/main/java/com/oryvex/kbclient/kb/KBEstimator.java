package com.oryvex.kbclient.kb;

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
