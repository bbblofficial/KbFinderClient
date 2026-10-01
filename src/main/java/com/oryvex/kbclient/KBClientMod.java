package com.oryvex.kbclient;

import com.oryvex.kbclient.ui.Fade;
import com.oryvex.kbclient.ui.FadeScreen;
import com.oryvex.kbclient.ui.GuiAnalyzer;
import com.oryvex.kbclient.ui.GuiModernMenu;
import com.oryvex.kbclient.ui.Hud;
import com.oryvex.kbclient.ui.KBLoading;
import com.oryvex.kbclient.ui.LoadingArt;
import com.oryvex.kbclient.ui.Settings;
import com.oryvex.kbclient.ui.UiButton;
import io.netty.channel.Channel;
import io.netty.channel.ChannelDuplexHandler;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelPipeline;
import net.minecraft.client.Minecraft;
import net.minecraft.client.entity.EntityPlayerSP;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiChat;
import net.minecraft.client.gui.GuiDisconnected;
import net.minecraft.client.gui.GuiDownloadTerrain;
import net.minecraft.client.gui.GuiIngameMenu;
import net.minecraft.client.gui.GuiMainMenu;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.inventory.GuiContainer;
import net.minecraft.client.multiplayer.GuiConnecting;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.settings.KeyBinding;
import net.minecraft.network.NetworkManager;
import net.minecraft.network.play.server.S12PacketEntityVelocity;
import net.minecraftforge.client.ClientCommandHandler;
import net.minecraftforge.client.event.GuiOpenEvent;
import net.minecraftforge.client.event.GuiScreenEvent;
import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.client.registry.ClientRegistry;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.Mod.EventHandler;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
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
    public static final String VERSION = "1.0.0";
    private static final String HOOK = "kb_client_handler";
    private static final int RECONNECT_BTN_ID = 9001;

    private static KBClientMod instance;
    public static Logger logger;

    private final KBTracker tracker = new KBTracker();
    private KeyBinding openKey;
    private Channel hookedChannel;
    private boolean pendingOpen;
    private Object lastWorld;
    private boolean loadingInstalled;
    public static net.minecraft.client.multiplayer.ServerData lastServerData;
    private boolean hasFakeLoaded = false;
    private ServerData lastServer;

    public static KBClientMod getInstance() { return instance; }
    public KBTracker getTracker() { return tracker; }

    public void requestOpenAnalyzer() { pendingOpen = true; }

    @EventHandler
    public void preInit(FMLPreInitializationEvent e) {
        logger = e.getModLog();
        instance = this;
        Settings.load();
    }

    @EventHandler
    public void init(FMLInitializationEvent e) {
        com.oryvex.kbclient.GuiStateFixer __fix = new com.oryvex.kbclient.GuiStateFixer();
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.register(__fix);
        net.minecraftforge.fml.common.FMLCommonHandler.instance().bus().register(__fix);
        MinecraftForge.EVENT_BUS.register(this);
        ClientCommandHandler.instance.registerCommand(new KBCommand());
        openKey = new KeyBinding("Open KB Analyzer", Keyboard.KEY_RSHIFT, "KB Client");
        ClientRegistry.registerKeyBinding(openKey);
        installLoading();
        DiscordRPC.start();
    }

    private void installLoading() {
        if (loadingInstalled) return;
        Minecraft mc = Minecraft.getMinecraft();
        try {
            ObfuscationReflectionHelper.setPrivateValue(Minecraft.class, mc, new KBLoading(mc), "loadingScreen", "field_71461_s");
            loadingInstalled = true;
            logger.info("[KBClient] custom loading screen installed");
        } catch (Throwable t) {
            logger.error("[KBClient] could not install loading screen: " + t);
        }
    }

    @SubscribeEvent
    public void onGuiOpen(GuiOpenEvent e) {
        Minecraft mc = Minecraft.getMinecraft();
        if (e.gui instanceof GuiMainMenu) {
            if (!hasFakeLoaded) {
                e.gui = new com.oryvex.kbclient.ui.GuiFakeLoading(tracker);
                hasFakeLoaded = true;
            } else {
                e.gui = new GuiModernMenu(tracker);
            }
        }

        if (e.gui == null) {
            if (mc.theWorld != null && !(mc.currentScreen instanceof GuiChat) && !(mc.currentScreen instanceof GuiContainer)) {
                Fade.world.trigger(0.45f);
            }
        } else if (!(e.gui instanceof FadeScreen) && (!(e.gui instanceof GuiChat)) && !(e.gui instanceof com.oryvex.kbclient.ui.GuiFakeLoading) && !(e.gui instanceof com.oryvex.kbclient.ui.GuiFakeWorldLoad)) {
            Fade.screen.trigger(e.gui instanceof GuiContainer ? 0.35f : 0.75f);
        }
    }

    @SubscribeEvent
    public void onDrawScreen(GuiScreenEvent.DrawScreenEvent.Post e) {
        GuiScreen g = e.gui;
        if (g == null || g instanceof FadeScreen) return;
        if (Settings.customLoading && g instanceof GuiDownloadTerrain) {
            LoadingArt.draw(g.width, g.height, "Joining world", "Downloading terrain", -1);
        }
        Fade.screen.draw(g.width, g.height);
    }

        @SubscribeEvent
    public void onInitGui(GuiScreenEvent.InitGuiEvent.Post e) {
        if (e.gui instanceof GuiIngameMenu) {
            for (int i = 0; i < e.buttonList.size(); i++) {
                net.minecraft.client.gui.GuiButton b = e.buttonList.get(i);
                if (b.id == 0) {
                    UiButton u = new UiButton(0, b.xPosition, b.yPosition, b.width, b.height, b.displayString);
                    u.icon = UiButton.ICON_GEAR;
                    e.buttonList.set(i, u);
                }
            }
        } else if (e.gui instanceof net.minecraft.client.gui.GuiDisconnected) {
            for (net.minecraft.client.gui.GuiButton b : e.buttonList) {
                if (b.id == 0) { // دکمه Back دیفالت ماینکرفت
                    e.buttonList.add(new UiButton(999, b.xPosition, b.yPosition + b.height + 6, b.width, b.height, "Reconnect").style(UiButton.PRIMARY));
                    break;
                }
            }
        }
    }
            }
            return;
        }

        if (e.gui instanceof GuiDisconnected) {
            int bw = 200, bh = 20;
            UiButton reconnect = new UiButton(RECONNECT_BTN_ID, e.gui.width / 2 - bw / 2, e.gui.height / 4 + 108, bw, bh, "Reconnect");
            reconnect.style(UiButton.PRIMARY);
            reconnect.enabled = lastServer != null;
            e.buttonList.add(reconnect);
        }
    }

    /** Handles our injected "Reconnect" button on the Disconnected screen. */
    @SubscribeEvent
    public void onAction(GuiScreenEvent.ActionPerformedEvent.Pre e) {
        if (!(e.gui instanceof GuiDisconnected) || e.button == null || e.button.id != RECONNECT_BTN_ID) return;
        e.setCanceled(true);
        if (lastServer != null) {
            Minecraft.getMinecraft().displayGuiScreen(new GuiConnecting(e.gui, Minecraft.getMinecraft(), lastServer));
        }
    }

    
        @SubscribeEvent
    public void onActionPerformed(net.minecraftforge.client.event.GuiScreenEvent.ActionPerformedEvent.Pre e) {
        if (e.gui instanceof GuiIngameMenu && e.button.id == 0) {
            e.setCanceled(true);
            net.minecraft.client.Minecraft.getMinecraft().displayGuiScreen(new com.oryvex.kbclient.ui.GuiKbOptions(tracker, e.gui));
        } else if (e.gui instanceof net.minecraft.client.gui.GuiDisconnected && e.button.id == 999) {
            if (lastServerData != null) {
                net.minecraft.client.Minecraft mc = net.minecraft.client.Minecraft.getMinecraft();
                mc.displayGuiScreen(new net.minecraft.client.multiplayer.GuiConnecting(new com.oryvex.kbclient.ui.GuiModernMenu(tracker), mc, lastServerData));
            }
        }
    }

    @SubscribeEvent
    public void onOverlay(RenderGameOverlayEvent.Post e) {
        if (e.type != RenderGameOverlayEvent.ElementType.ALL) return;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.thePlayer == null) return;
        if (!mc.gameSettings.showDebugInfo && !(mc.currentScreen instanceof GuiAnalyzer)) Hud.render(mc, tracker);
        Fade.world.draw(e.resolution.getScaledWidth(), e.resolution.getScaledHeight());
    }

    @SubscribeEvent
    public void onTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getMinecraft();
        if (mc.getCurrentServerData() != null) lastServerData = mc.getCurrentServerData();
        tracker.tick();
        DiscordRPC.tick();

        if (mc.theWorld != lastWorld) {
            lastWorld = mc.theWorld;
            if (mc.theWorld != null) {
                if (Fade.ms() > 0) Fade.world.trigger(1f, Fade.ms() * 3L);
                mc.displayGuiScreen(new com.oryvex.kbclient.ui.GuiFakeWorldLoad());
            }
        }

        while (openKey.isPressed()) {
            if (mc.currentScreen == null) pendingOpen = true;
        }
        if (pendingOpen && mc.currentScreen == null) {
            pendingOpen = false;
            mc.displayGuiScreen(new GuiAnalyzer(tracker, null));
        }

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
            if (!mc.isSingleplayer() && mc.getCurrentServerData() != null) lastServer = mc.getCurrentServerData();
            tracker.onConnect(name);
            logger.info("[KBClient] velocity hook installed on " + name);
        } catch (Throwable t) {
            logger.error("[KBClient] hook failed: " + t);
        }
    }

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