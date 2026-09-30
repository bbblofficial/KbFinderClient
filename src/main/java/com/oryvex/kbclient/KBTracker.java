package com.oryvex.kbclient;

import com.oryvex.kbclient.kb.KBEstimator;
import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBSample;
import com.oryvex.kbclient.ui.Hud;
import com.oryvex.kbclient.ui.Theme;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.enchantment.EnchantmentHelper;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.util.ChatComponentText;

/** Collects knockback samples (main thread only) and keeps a live profile. */
public class KBTracker {
    public static final int MAX_SAMPLES = 120;

    private final List<KBSample> samples = new ArrayList<KBSample>();
    private KBProfile profile = new KBProfile();
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

    public void tick() { tick++; }

    public synchronized KBProfile getProfile() { return profile; }
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

    /** Must be called on the client main thread, BEFORE the packet is applied. */
    public synchronized void capture(int rawX, int rawY, int rawZ) {
        Minecraft mc = Minecraft.getMinecraft();
        EntityPlayerSP me = mc.thePlayer;
        if (!recording || me == null || mc.theWorld == null) return;

        double vx = rawX / 8000.0, vy = rawY / 8000.0, vz = rawZ / 8000.0;
        double h = Math.sqrt(vx * vx + vz * vz);

        // attacker = nearby player best aligned with the knockback direction
        EntityPlayer attacker = null;
        double bestScore = -1.0e9;
        for (EntityPlayer e : mc.theWorld.playerEntities) {
            if (e == me || e.isDead) continue;
            double dist = me.getDistanceToEntity(e);
            if (dist > 7.0) continue;
            double dx = me.posX - e.posX, dz = me.posZ - e.posZ;
            double dh = Math.sqrt(dx * dx + dz * dz);
            double score = -dist * 0.05;
            if (h > 0.05 && dh > 0.001) score += (vx * dx + vz * dz) / (h * dh);
            if (score > bestScore) { bestScore = score; attacker = e; }
        }

        boolean has = attacker != null;
        double ux = 0, uz = 0, dist = 0;
        boolean aSprint = false;
        int kb = 0;
        String name = "?";
        if (has) {
            double dx = me.posX - attacker.posX, dz = me.posZ - attacker.posZ;
            double dh = Math.sqrt(dx * dx + dz * dz);
            if (dh > 0.001) { ux = dx / dh; uz = dz / dh; }
            else if (h > 0.001) { ux = vx / h; uz = vz / h; }
            aSprint = attacker.isSprinting();
            try { kb = EnchantmentHelper.getKnockbackModifier(attacker); } catch (Throwable ignored) { }
            name = attacker.getName();
            dist = me.getDistanceToEntity(attacker);
        }

        KBSample s = new KBSample(nextId++, tick, vx, vy, vz,
                me.motionX, me.motionY, me.motionZ, me.isSprinting(), me.onGround,
                has, aSprint, kb, ux, uz, dist, name);

        samples.add(s);
        while (samples.size() > MAX_SAMPLES) samples.remove(0);
        last = s;
        profile = KBEstimator.calculate(samples);

        String tag = has ? (aSprint ? "SPRINT" : "WALK") : "no attacker";
        int col = has ? (aSprint ? Theme.WARN : Theme.GOOD) : Theme.DIM;
        Hud.push("Hit #" + s.id + "  H " + KBProfile.f(h, 4) + "  V " + KBProfile.f(vy, 4) + "  " + tag, col);

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
        chat(g + "HORIZONTAL: " + w + KBProfile.f(p.horizontal, 4) + g + "   EXTRA-H: " + w + KBProfile.f(p.extraHorizontal, 4));
        chat(g + "VERTICAL: " + w + KBProfile.f(p.vertical, 4) + g + "   EXTRA-V: " + w + KBProfile.f(p.extraVertical, 4));
        chat(g + "FRICTION: " + w + KBProfile.f(p.friction, 3) + g + "   Y-LIMIT: " + w + KBProfile.f(p.yLimit, 3));
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
        sb.append("id,tick,vx,vy,vz,h,prevX,prevY,prevZ,prevH,victimSprint,victimGround,attacker,attackerSprint,attackerKb,distance,ux,uz\n");
        for (KBSample k : samples) {
            sb.append(k.id).append(',').append(k.tick).append(',')
              .append(KBProfile.f(k.vx, 5)).append(',').append(KBProfile.f(k.vy, 5)).append(',')
              .append(KBProfile.f(k.vz, 5)).append(',').append(KBProfile.f(k.h, 5)).append(',')
              .append(KBProfile.f(k.px, 5)).append(',').append(KBProfile.f(k.py, 5)).append(',')
              .append(KBProfile.f(k.pz, 5)).append(',').append(KBProfile.f(k.pH, 5)).append(',')
              .append(k.victimSprint).append(',').append(k.victimGround).append(',')
              .append(k.attacker.replace(',', '_')).append(',').append(k.attackerSprint).append(',')
              .append(k.attackerKb).append(',').append(KBProfile.f(k.distance, 3)).append(',')
              .append(KBProfile.f(k.ux, 4)).append(',').append(KBProfile.f(k.uz, 4)).append('\n');
        }
        File csv = new File(dir, "knockback-" + ts + "-samples.csv");
        Files.write(csv.toPath(), sb.toString().getBytes(StandardCharsets.UTF_8));
        return yml;
    }
}
