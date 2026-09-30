package com.oryvex.kbclient.kb;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Exact reader for the Carbon knockback config.
 * Handles: full-line and inline comments, nested sections (DAMAGE-TICKS -> OVERRIDE/VALUE),
 * dotted keys, inline maps ({OVERRIDE: false, VALUE: 17}), quotes, booleans, decimals, ints.
 * Every one of the 12 keys is looked up; anything missing or unparsable is reported, never guessed.
 */
public final class KBYaml {
    private KBYaml() {}

    public static final String SAMPLE =
        "# Should we use 1.7 Knockback?\n"
      + "ONE-POINT-SEVEN: false\n\n"
      + "# Horizontal Multiplier\n"
      + "HORIZONTAL: 0.3618\n\n"
      + "# Vertical Value\n"
      + "VERTICAL: 0.4861\n\n"
      + "# Add a certain value to horizontal/vertical before actual calculations\n"
      + "EXTRA-HORIZONTAL: 0.5553\n"
      + "EXTRA-VERTICAL: 0.0\n\n"
      + "# Friction Value (Knockback is divided by this)\n"
      + "FRICTION: 2.0\n\n"
      + "# Y-Axis Limit for a player's velocity\n"
      + "Y-LIMIT: 0.439\n\n"
      + "DAMAGE-TICKS:\n"
      + "  # Override vanilla damage ticks with carbon's\n"
      + "  OVERRIDE: false\n"
      + "  # The delay between a player's ability to damage an entity\n"
      + "  VALUE: 17\n\n"
      + "# Should the vertical velocity be set to 0 after reaching limit?\n"
      + "DYNAMIC-LIMIT: false\n\n"
      + "# Should we limit horizontal movement?\n"
      + "LIMIT-HORIZONTAL: false\n\n"
      + "# X/Z-Axis Limit for a player's velocity\n"
      + "H-LIMIT: 0.897\n";

    public static final class Result {
        public final Map<String, String> raw = new LinkedHashMap<String, String>();
        public final List<String> missing = new ArrayList<String>();
        public final List<String> errors = new ArrayList<String>();
        public final List<String> unknown = new ArrayList<String>();
        public KBProfile profile = new KBProfile();
        public int parsed;

        public boolean complete() { return missing.isEmpty() && errors.isEmpty(); }

        public String summary() {
            StringBuilder sb = new StringBuilder();
            sb.append(parsed).append('/').append(KBProfile.COUNT).append(" keys parsed");
            if (!missing.isEmpty()) sb.append(", missing ").append(missing);
            if (!errors.isEmpty()) sb.append(", errors ").append(errors);
            return sb.toString();
        }
    }

    public static Result parse(String text) {
        Result r = new Result();
        if (text == null) text = "";
        if (text.length() > 0 && text.charAt(0) == '\uFEFF') text = text.substring(1);
        String[] lines = text.split("\r\n|\r|\n", -1);

        List<Integer> indents = new ArrayList<Integer>();
        List<String> names = new ArrayList<String>();

        for (int ln = 0; ln < lines.length; ln++) {
            String line = stripComment(lines[ln]);
            if (line.trim().isEmpty()) continue;
            int indent = 0;
            for (int i = 0; i < line.length(); i++) {
                char c = line.charAt(i);
                if (c == ' ') indent++;
                else if (c == '\t') indent += 2;
                else break;
            }
            String body = line.trim();
            if (body.equals("---") || body.equals("...")) continue;
            if (body.startsWith("- ")) { r.errors.add("line " + (ln + 1) + ": lists are not supported"); continue; }
            int colon = indexOfColon(body);
            if (colon <= 0) { r.errors.add("line " + (ln + 1) + ": expected 'KEY: value'"); continue; }

            String key = norm(body.substring(0, colon));
            String val = body.substring(colon + 1).trim();

            while (!indents.isEmpty() && indents.get(indents.size() - 1) >= indent) {
                indents.remove(indents.size() - 1);
                names.remove(names.size() - 1);
            }
            StringBuilder path = new StringBuilder();
            for (String n : names) path.append(n).append('.');
            String full = path + key;

            if (val.isEmpty()) { indents.add(indent); names.add(key); continue; }
            if (val.startsWith("{") && val.endsWith("}")) {
                String inner = val.substring(1, val.length() - 1);
                for (String part : inner.split(",")) {
                    int c = indexOfColon(part);
                    if (c > 0) r.raw.put(full + "." + norm(part.substring(0, c)), unquote(part.substring(c + 1).trim()));
                }
                continue;
            }
            r.raw.put(full, unquote(val));
        }

        KBProfile p = r.profile;
        for (int i = 0; i < KBProfile.COUNT; i++) {
            String v = r.raw.get(KBProfile.KEYS[i]);
            if (v == null) { r.missing.add(KBProfile.KEYS[i]); continue; }
            try {
                p.setFromText(i, v);
                r.parsed++;
            } catch (NumberFormatException e) {
                r.errors.add(KBProfile.KEYS[i] + ": cannot parse '" + v + "'");
            }
        }
        for (String k : r.raw.keySet()) {
            boolean known = false;
            for (String kk : KBProfile.KEYS) if (kk.equals(k)) { known = true; break; }
            if (!known) r.unknown.add(k);
        }
        p.hasData = r.parsed > 0;
        return r;
    }

    private static String stripComment(String line) {
        char q = 0;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (q != 0) { if (c == q) q = 0; }
            else if (c == '"' || c == '\'') q = c;
            else if (c == '#' && (i == 0 || Character.isWhitespace(line.charAt(i - 1)))) return line.substring(0, i);
        }
        return line;
    }

    private static int indexOfColon(String s) {
        char q = 0;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (q != 0) { if (c == q) q = 0; }
            else if (c == '"' || c == '\'') q = c;
            else if (c == ':') return i;
        }
        return -1;
    }

    private static String unquote(String s) {
        s = s.trim();
        if (s.length() >= 2) {
            char a = s.charAt(0), b = s.charAt(s.length() - 1);
            if (a == b && (a == '"' || a == '\'')) return s.substring(1, s.length() - 1);
        }
        return s;
    }

    private static String norm(String k) {
        return unquote(k.trim()).toUpperCase(Locale.ROOT).replace('_', '-');
    }
}
