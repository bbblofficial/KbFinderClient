package com.oryvex.kbclient;

import com.oryvex.kbclient.ui.GuiAnalyzer;
import com.oryvex.kbclient.ui.GuiModernMenu;
import com.oryvex.kbclient.ui.Hud;
import io.netty.channel.Channel;
import io.netty.channel.ChannelDuplexHandler;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelPipeline;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.client.gui.GuiMainMenu;
import net.minecraft.client.settings.KeyBinding;
import net.minecraft.network.NetworkManager;
import net.minecraft.network.play.server.S12PacketEntityVelocity;
import net.minecraftforge.client.ClientCommandHandler;
import net.minecraftforge.client.event.GuiOpenEvent;
import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.client.registry.ClientRegistry;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.Mod.EventHandler;
import net.minecraftforge.fml.common.event.FMLInitializationEvent;
import net.minecraftforge.fml.common.event.FMLPreInitializationEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import net.minecraftforge.fml.common.gameevent.TickEvent;
import org.apache.logging.log4j.Logger;
import org.lwjgl.input.Keyboard;

@Mod(modid = KBClientMod.MODID, name = KBClientMod.NAME, version = KBClientMod.VERSION,
     acceptedMinecraftVersions = "[1.8.9]", clientSideOnly = true)
public class KBClientMod {
    public static final String MODID = "kbclient";
    public static final String NAME = "KB Client";
    public static final String VERSION = "2.0.0";
    private static final String HOOK = "kb_client_handler";

    private static KBClientMod instance;
    public static Logger logger;

    private final KBTracker tracker = new KBTracker();
    private KeyBinding openKey;
    private Channel hookedChannel;
    private boolean pendingOpen;
    private boolean hud = true;

    public static KBClientMod getInstance() { return instance; }
    public KBTracker getTracker() { return tracker; }
    public boolean isHud() { return hud; }
    public void setHud(boolean h) { hud = h; }

    /** Opened on the next tick, because chat closes itself right after running a command. */
    public void requestOpenAnalyzer() { pendingOpen = true; }

    @EventHandler
    public void preInit(FMLPreInitializationEvent e) {
        logger = e.getModLog();
        instance = this;
    }

    @EventHandler
    public void init(FMLInitializationEvent e) {
        MinecraftForge.EVENT_BUS.register(this);
        ClientCommandHandler.instance.registerCommand(new KBCommand());
        openKey = new KeyBinding("Open KB Analyzer", Keyboard.KEY_RSHIFT, "KB Client");
        ClientRegistry.registerKeyBinding(openKey);
    }

    @SubscribeEvent
    public void onGuiOpen(GuiOpenEvent e) {
        if (e.gui instanceof GuiMainMenu) e.gui = new GuiModernMenu(tracker);
    }

    @SubscribeEvent
    public void onOverlay(RenderGameOverlayEvent.Post e) {
        if (e.type != RenderGameOverlayEvent.ElementType.ALL || !hud) return;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.thePlayer == null || mc.gameSettings.showDebugInfo || mc.currentScreen instanceof GuiAnalyzer) return;
        Hud.render(mc, tracker);
    }

    @SubscribeEvent
    public void onTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getMinecraft();
        tracker.tick();

        while (openKey.isPressed()) {
            if (mc.currentScreen == null) pendingOpen = true;
        }
        if (pendingOpen && mc.currentScreen == null) {
            pendingOpen = false;
            mc.displayGuiScreen(new GuiAnalyzer(tracker, null));
        }

        // (re)hook the network pipeline whenever the connection changes
        if (mc.thePlayer != null && mc.thePlayer.sendQueue != null) {
            NetworkManager nm = mc.thePlayer.sendQueue.getNetworkManager();
            if (nm != null && nm.channel() != null && nm.channel() != hookedChannel) inject(mc, nm.channel());
        }
    }

    private void inject(Minecraft mc, Channel ch) {
        hookedChannel = ch;
        try {
            ChannelPipeline pl = ch.pipeline();
            if (pl.get(HOOK) != null) pl.remove(HOOK);
            if (pl.get("packet_handler") != null) pl.addBefore("packet_handler", HOOK, new VelocityHook());
            else pl.addLast(HOOK, new VelocityHook());

            String name = mc.isSingleplayer() ? "Singleplayer"
                    : (mc.getCurrentServerData() != null ? mc.getCurrentServerData().serverIP : "Server");
            tracker.onConnect(name);
            logger.info("[KBClient] velocity hook installed on " + name);
        } catch (Throwable t) {
            logger.error("[KBClient] hook failed: " + t);
        }
    }

    /** Sits before the vanilla handler, queues a main-thread task that runs BEFORE the packet is applied. */
    private static class VelocityHook extends ChannelDuplexHandler {
        @Override
        public void channelRead(ChannelHandlerContext ctx, Object msg) throws Exception {
            if (msg instanceof S12PacketEntityVelocity) {
                S12PacketEntityVelocity v = (S12PacketEntityVelocity) msg;
                final int id = v.getEntityID();
                final int x = v.getMotionX(), y = v.getMotionY(), z = v.getMotionZ();
                final Minecraft mc = Minecraft.getMinecraft();
                mc.addScheduledTask(new Runnable() {
                    @Override
                    public void run() {
                        EntityPlayerSP p = mc.thePlayer;
                        if (p != null && p.getEntityId() == id) {
                            KBClientMod.getInstance().getTracker().capture(x, y, z);
                        }
                    }
                });
            }
            super.channelRead(ctx, msg);
        }
    }
}
