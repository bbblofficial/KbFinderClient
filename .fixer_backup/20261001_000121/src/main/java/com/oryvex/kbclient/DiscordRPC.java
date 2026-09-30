package com.oryvex.kbclient;

import club.minnced.discord.rpc.DiscordEventHandlers;
import club.minnced.discord.rpc.DiscordRPC;
import club.minnced.discord.rpc.DiscordRichPresence;
import net.minecraft.client.Minecraft;

/**
 * Discord Rich Presence for KB Client.
 *
 * Create a Discord Application at https://discord.com/developers/applications
 * and put its Application ID into APP_ID below. Upload image assets named
 * "oryvex" and "minecraft" in the Rich Presence -> Art Assets tab.
 */
public final class DiscordRPC {
    /** TODO: replace with your own Discord Application ID. */
    private static final String APP_ID = "1554952903758716989";

    private static club.minnced.discord.rpc.DiscordRPC rpc;
    private static DiscordRichPresence presence;
    private static Thread worker;
    private static volatile boolean running;
    private static long startTime;
    private static String lastDetails = "";
    private static String lastState = "";

    private DiscordRPC() {}

    public static synchronized void start() {
        if (running) return;
        if (APP_ID.startsWith("1234")) {
            KBClientMod.logger.warn("[KBClient] Discord RPC disabled: set your APP_ID in DiscordRPC.java");
            return;
        }
        try {
            rpc = club.minnced.discord.rpc.DiscordRPC.INSTANCE;

            DiscordEventHandlers handlers = new DiscordEventHandlers();
            handlers.ready = user -> KBClientMod.logger.info("[KBClient] Discord RPC ready for " + user.username);
            handlers.disconnected = (code, msg) -> KBClientMod.logger.warn("[KBClient] Discord RPC disconnected: " + code + " " + msg);
            handlers.errored = (code, msg) -> KBClientMod.logger.warn("[KBClient] Discord RPC error: " + code + " " + msg);

            rpc.Discord_Initialize(APP_ID, handlers, true, null);

            startTime = System.currentTimeMillis() / 1000L;
            presence = new DiscordRichPresence();
            presence.startTimestamp = startTime;
            presence.largeImageKey = "oryvex";
            presence.largeImageText = "KB Client 3.0";
            presence.smallImageKey = "minecraft";
            presence.smallImageText = "Minecraft 1.8.9";
            presence.details = "In the menus";
            presence.state = "Idle";
            rpc.Discord_UpdatePresence(presence);

            running = true;
            worker = new Thread(DiscordRPC::loop, "KBClient-DiscordRPC");
            worker.setDaemon(true);
            worker.start();

            KBClientMod.logger.info("[KBClient] Discord RPC started");
        } catch (Throwable t) {
            KBClientMod.logger.error("[KBClient] Discord RPC init failed: " + t);
        }
    }

    private static void loop() {
        while (running) {
            try {
                rpc.Discord_RunCallbacks();
                updatePresence();
                Thread.sleep(2000L);
            } catch (InterruptedException e) {
                break;
            } catch (Throwable t) {
                KBClientMod.logger.warn("[KBClient] Discord RPC loop error: " + t);
            }
        }
    }

    private static void updatePresence() {
        Minecraft mc = Minecraft.getMinecraft();
        String details;
        String state;

        if (mc.theWorld == null) {
            details = "In the menus";
            state = "KB Client 3.0";
        } else if (mc.isSingleplayer()) {
            details = "Singleplayer";
            String worldName = "world";
            try {
                if (mc.getIntegratedServer() != null) worldName = mc.getIntegratedServer().getWorldName();
            } catch (Throwable ignored) { }
            state = "World: " + worldName;
        } else {
            String ip = (mc.getCurrentServerData() != null)
                    ? mc.getCurrentServerData().serverIP
                    : "Unknown server";
            details = "Playing on " + ip;
            int players = (mc.theWorld != null) ? mc.theWorld.playerEntities.size() : 0;
            state = players + " players online";
        }

        if (details.equals(lastDetails) && state.equals(lastState)) return;
        lastDetails = details;
        lastState = state;

        presence.details = details;
        presence.state = state;
        presence.startTimestamp = startTime;
        rpc.Discord_UpdatePresence(presence);
    }

    public static synchronized void stop() {
        if (!running) return;
        running = false;
        try {
            if (worker != null) worker.interrupt();
            if (rpc != null) {
                rpc.Discord_ClearPresence();
                rpc.Discord_Shutdown();
            }
        } catch (Throwable ignored) { }
        rpc = null;
        presence = null;
        KBClientMod.logger.info("[KBClient] Discord RPC stopped");
    }

    public static boolean isRunning() {
        return running;
    }
}
