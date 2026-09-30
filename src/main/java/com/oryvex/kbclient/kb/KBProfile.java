package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Estimated Carbon/Spigot knockback configuration + confidence for each value. */
public final class KBProfile {
    public boolean onePointSeven = false;
    public double horizontal = 0.400;
    public double vertical = 0.400;
    public double extraHorizontal = 0.500;
    public double extraVertical = 0.000;
    public double friction = 2.000;
    public double yLimit = 0.400;
    public boolean damageTicksOverride = false;
    public int damageTicksValue = 20;
    public boolean dynamicLimit = false;
    public boolean limitHorizontal = false;
    public double hLimit = 0.450;

    /** confidence 0..1 per value (0 = default / not measured) */
    public double cOps, cH, cV, cEH, cEV, cF, cYL, cHL, cLimH, cDyn, cDT;

    public int total, used, walk, sprint;
    public boolean hasData;
    public boolean frictionMeasured;
    public double hSpread, vSpread;
    public final List<String> notes = new ArrayList<String>();

    public static String f(double v, int decimals) {
        return String.format(Locale.ROOT, "%." + decimals + "f", v);
    }

    public String summary() {
        return "H " + f(horizontal, 4) + "  V " + f(vertical, 4) + "  F " + f(friction, 3);
    }

    public String toYaml() {
        StringBuilder sb = new StringBuilder();
        sb.append("ONE-POINT-SEVEN: ").append(onePointSeven).append("\n\n");
        sb.append("# Horizontal Multiplier\n");
        sb.append("HORIZONTAL: ").append(f(horizontal, 4)).append("\n\n");
        sb.append("# Vertical Value\n");
        sb.append("VERTICAL: ").append(f(vertical, 4)).append("\n\n");
        sb.append("# Add a certain value to horizontal/vertical before actual calculations\n");
        sb.append("EXTRA-HORIZONTAL: ").append(f(extraHorizontal, 4)).append("\n");
        sb.append("EXTRA-VERTICAL: ").append(f(extraVertical, 4)).append("\n\n");
        sb.append("# Friction Value (Knockback is divided by this)\n");
        sb.append("FRICTION: ").append(f(friction, 3)).append("\n\n");
        sb.append("# Y-Axis Limit for a player's velocity\n");
        sb.append("Y-LIMIT: ").append(f(yLimit, 3)).append("\n\n");
        sb.append("DAMAGE-TICKS:\n");
        sb.append("  # Override vanilla damage ticks with carbon's\n");
        sb.append("  OVERRIDE: ").append(damageTicksOverride).append("\n");
        sb.append("  # The delay between a player's ability to damage an entity\n");
        sb.append("  VALUE: ").append(damageTicksValue).append("\n\n");
        sb.append("# Should the vertical velocity be set to 0 after reaching limit?\n");
        sb.append("DYNAMIC-LIMIT: ").append(dynamicLimit).append("\n\n");
        sb.append("# Should we limit horizontal movement?\n");
        sb.append("LIMIT-HORIZONTAL: ").append(limitHorizontal).append("\n\n");
        sb.append("# X/Z-Axis Limit for a player's velocity\n");
        sb.append("H-LIMIT: ").append(f(hLimit, 3));
        return sb.toString();
    }
}
