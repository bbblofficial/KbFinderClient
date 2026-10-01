package com.oryvex.kbclient.kb;

/** One knockback event (velocity packet) plus the context it happened in. */
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

    public KBSample(int id, long tick, double vx, double vy, double vz,
                    double px, double py, double pz,
                    boolean victimSprint, boolean victimGround,
                    boolean hasAttacker, int sprintState, int attackerKb,
                    double ux, double uz, double distance, String attacker) {
        this.id = id;
        this.tick = tick;
        this.vx = vx;
        this.vy = vy;
        this.vz = vz;
        this.h = Math.sqrt(vx * vx + vz * vz);
        this.px = px;
        this.py = py;
        this.pz = pz;
        this.pH = Math.sqrt(px * px + pz * pz);
        this.victimSprint = victimSprint;
        this.victimGround = victimGround;
        this.hasAttacker = hasAttacker;
        this.sprintState = sprintState;
        this.attackerSprint = sprintState == SPRINT;
        this.attackerKb = attackerKb;
        this.ux = ux;
        this.uz = uz;
        this.distance = distance;
        this.attacker = attacker == null ? "?" : attacker;
    }
}
