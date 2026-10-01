package com.oryvex.kbclient.kb;

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
