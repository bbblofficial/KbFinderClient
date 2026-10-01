
package com.oryvex.kbclient.ui;

/** Frame-rate independent smoothing: chases a target value. */
public final class Anim {
    public float v;
    private long last = System.nanoTime();

    public Anim() {}
    public Anim(float start) { v = start; }

    /** speed ~ 8 (slow) .. 24 (snappy). Call once per frame. */
    public float to(float target, float speed) {
        long n = System.nanoTime();
        float dt = Math.min(0.1f, (n - last) / 1.0e9f);
        last = n;
        v += (target - v) * Math.min(1f, dt * speed);
        if (Math.abs(target - v) < 0.0006f) v = target;
        return v;
    }

    public void set(float x) {
        v = x;
        last = System.nanoTime();
    }
}
