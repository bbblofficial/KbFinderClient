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

/** 
 * Collects knockback samples (main thread only), keeps a live profile and an imported reference.
 * Optimized for high-precision data collection.
 */
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

    /** per client tick: remember the last 3 ticks of every player's sprint flag */
    public synchronized void tick() {
        tick++;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.theWorld == null) return;
        
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            int id = e.getEntityId();
            int s = e.isSprinting() ? 1 : 0;
            Integer b = sprintBits.get(id);
            // Store last 3 states in bits: 0x7 means all 3 were sprinting
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

        // Convert packet values to velocity
        double vx = rawX / 8000.0;
        double vy = rawY / 8000.0;
        double vz = rawZ / 8000.0;
        
        // Calculate horizontal magnitude
        double h = Math.sqrt(vx * vx + vz * vz);
        
        // Filter out tiny noise packets that are not real knockback
        if (h < 0.001 && Math.abs(vy) < 0.001) return;

        EntityPlayer attacker = null;
        double bestScore = -1.0e9;
        
        // Precise attacker identification using distance and vector alignment
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            if (e == me || e.isDead || e.getDistanceToEntity(me) > 6.0) continue; // Reduced range for precision
            
            double dx = me.posX - e.posX;
            double dz = me.posZ - e.posZ;
            double distSq = dx*dx + dz*dz;
            
            // Score based on proximity and direction alignment
            double score = -distSq * 0.1; 
            if (h > 0.01) {
                // Dot product to check if velocity direction matches player direction
                double dot = (vx * dx + vz * dz);
                score += dot / (h * Math.sqrt(distSq)); 
            }
            
            if (score > bestScore) {
                bestScore = score;
                attacker = e;
            }
        }

        boolean hasAttacker = attacker != null;
        double ux = 0, uz = 0, dist = 0;
        int state = KBSample.WALK;
        int kbEnchant = 0;
        String name = "?";

        if (hasAttacker) {
            double dx = me.posX - attacker.posX;
            double dz = me.posZ - attacker.posZ;
            double dh = Math.sqrt(dx * dx + dz * dz);
            
            if (dh > 0.001) {
                ux = dx / dh;
                uz = dz / dh;
            } else {
                // Fallback to velocity direction if positions overlap
                if (h > 0.001) { ux = vx / h; uz = vz / h; }
            }
            
            // Precise sprint detection using bit history
            Integer bits = sprintBits.get(attacker.getEntityId());
            if (bits == null) {
                state = attacker.isSprinting() ? KBSample.SPRINT : KBSample.WALK;
            } else if (bits == 0x7) { // Last 3 ticks were sprinting
                state = KBSample.SPRINT;
            } else if (bits == 0) { // Last 3 ticks were walking
                state = KBSample.WALK;
            } else {
                state = KBSample.AMBIGUOUS; // W-tap or changing state
            }

            try { 
                kbEnchant = EnchantmentHelper.getKnockbackModifier(attacker); 
            } catch (Throwable ignored) { }
            
            name = attacker.getName();
            dist = me.getDistanceToEntity(attacker);
        }

        // Create sample
        KBSample s = new KBSample(nextId++, tick, vx, vy, vz,
                me.motionX, me.motionY, me.motionZ, me.isSprinting(), me.onGround,
                hasAttacker, state, kbEnchant, ux, uz, dist, name);
                
        samples.add(s);
        
        // Keep more samples for better statistical analysis
        while (samples.size() > MAX_SAMPLES) samples.remove(0);
        
        last = s;
        
        // Recalculate profile with high-precision estimator
        profile = KBEstimator.calculate(samples);
        
        // HUD Update
        String tag = !hasAttacker ? "no attacker" : (state == KBSample.AMBIGUOUS ? "W-TAP?" : (state == KBSample.SPRINT ? "SPRINT" : "WALK"));
        int col = !hasAttacker ? Theme.DIM : (state == KBSample.AMBIGUOUS ? Theme.DIM : (state == KBSample.SPRINT ? Theme.WARN : Theme.GOOD));
        Hud.push("Hit #" + s.id + " H:" + KBProfile.f(h, 4) + " V:" + KBProfile.f(vy, 4) + " [" + tag + "]", col);

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