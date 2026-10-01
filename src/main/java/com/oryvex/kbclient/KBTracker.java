package com.oryvex.kbclient;

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
    public static final int MAX_SAMPLES = 200;
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

    /** Captures knockback using PRE-CALCULATED old motion to avoid packet application race conditions */
    public synchronized void capture(int rawX, int rawY, int rawZ, double oldX, double oldY, double oldZ, boolean oldGround, boolean oldSprint) {
        Minecraft mc = Minecraft.getMinecraft();
        EntityPlayerSP me = mc.thePlayer;
        if (!recording || me == null || mc.theWorld == null) return;

        double vx = rawX / 8000.0, vy = rawY / 8000.0, vz = rawZ / 8000.0;
        double h = Math.sqrt(vx * vx + vz * vz);
        if (h < 0.001 && Math.abs(vy) < 0.001) return;

        EntityPlayer attacker = null;
        double bestScore = -1.0e9;
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            if (e == me || e.isDead) continue;
            double dist = me.getDistanceToEntity(e);
            if (dist > 6.0) continue;
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

        // Use the safely captured old motion
        KBSample s = new KBSample(nextId++, tick, vx, vy, vz,
                oldX, oldY, oldZ, oldSprint, oldGround,
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
        Files.write(yml.toPath(), (profile.toYaml() + "\n").getBytes(StandardCharsets.UTF_8));
        return yml;
    }
}
