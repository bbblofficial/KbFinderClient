import os

def delete_rpc_files():
    base_dir = os.path.join("src", "main", "java", "com", "oryvex", "kbclient")
    ui_dir = os.path.join(base_dir, "ui")

    # 1. Delete DiscordRPC.java
    rpc_file = os.path.join(base_dir, "DiscordRPC.java")
    if os.path.exists(rpc_file):
        os.remove(rpc_file)
        print(f"Deleted: {rpc_file}")
    else:
        print(f"File not found (already deleted?): {rpc_file}")

    # 2. Revert KBClientMod.java
    kbclient_mod_path = os.path.join(base_dir, "KBClientMod.java")
    kbclient_mod_code = r"""package com.oryvex.kbclient;

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
import net.minecraft.client.gui.GuiDownloadTerrain;
import net.minecraft.client.gui.GuiIngameMenu;
import net.minecraft.client.gui.GuiMainMenu;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.inventory.GuiContainer;
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
    public static final String VERSION = "3.0.0";
    private static final String HOOK = "kb_client_handler";

    private static KBClientMod instance;
    public static Logger logger;

    private final KBTracker tracker = new KBTracker();
    private KeyBinding openKey;
    private Channel hookedChannel;
    private boolean pendingOpen;
    private Object lastWorld;
    private boolean loadingInstalled;

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
        if (e.gui instanceof GuiMainMenu) e.gui = new GuiModernMenu(tracker);

        if (e.gui == null) {
            if (mc.theWorld != null && !(mc.currentScreen instanceof GuiChat) && !(mc.currentScreen instanceof GuiContainer)) {
                Fade.world.trigger(0.45f);
            }
        } else if (!(e.gui instanceof FadeScreen) && !(e.gui instanceof GuiChat)) {
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
        if (!(e.gui instanceof GuiIngameMenu)) return;
        for (int i = 0; i < e.buttonList.size(); i++) {
            GuiButton b = e.buttonList.get(i);
            if (b.id == 0) {
                UiButton u = new UiButton(0, b.xPosition, b.yPosition, b.width, b.height, b.displayString);
                u.icon = UiButton.ICON_GEAR;
                e.buttonList.set(i, u);
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
        tracker.tick();

        if (mc.theWorld != lastWorld) {
            lastWorld = mc.theWorld;
            if (mc.theWorld != null && Fade.ms() > 0) Fade.world.trigger(1f, Fade.ms() * 3L);
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
"""
    with open(kbclient_mod_path, "w", encoding="utf-8") as f:
        f.write(kbclient_mod_code)
    print(f"Reverted: {kbclient_mod_path}")

    # 3. Revert GuiKbOptions.java
    options_path = os.path.join(ui_dir, "GuiKbOptions.java")
    options_code = r"""package com.oryvex.kbclient.ui;

import com.oryvex.kbclient.KBTracker;
import java.io.IOException;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiOptions;
import net.minecraft.client.gui.GuiScreen;

public class GuiKbOptions extends FadeScreen {
    private final KBTracker tracker;
    private final GuiScreen parent;
    private UiButton bHud, bPart, bToast, bLoad, bFade;
    private int cardX, cardY, cardW, cardH;

    public GuiKbOptions(KBTracker tracker, GuiScreen parent) {
        this.tracker = tracker;
        this.parent = parent;
    }

    @Override
    public void initGui() {
        this.buttonList.clear();
        int bw = 216, bh = 20, gap = 6, cx = this.width / 2;
        int y = Math.max(58, this.height / 2 - 78);
        cardW = bw + 28;
        cardX = cx - cardW / 2;
        cardY = y - 42;
        cardH = 7 * (bh + gap) + 62;

        bHud = new UiButton(1, cx - bw / 2, y, bw, bh, "HUD overlay").style(UiButton.TOGGLE).delay(60);
        bPart = new UiButton(2, cx - bw / 2, y + (bh + gap), bw, bh, "Menu particles").style(UiButton.TOGGLE).delay(110);
        bToast = new UiButton(3, cx - bw / 2, y + 2 * (bh + gap), bw, bh, "Hit toasts").style(UiButton.TOGGLE).delay(160);
        bLoad = new UiButton(4, cx - bw / 2, y + 3 * (bh + gap), bw, bh, "Custom loading screen").style(UiButton.TOGGLE).delay(210);
        bFade = new UiButton(5, cx - bw / 2, y + 4 * (bh + gap), bw, bh, "").delay(260);
        
        this.buttonList.add(bHud);
        this.buttonList.add(bPart);
        this.buttonList.add(bToast);
        this.buttonList.add(bLoad);
        this.buttonList.add(bFade);
        this.buttonList.add(new UiButton(6, cx - bw / 2, y + 5 * (bh + gap) + 8, bw, bh, "Minecraft Options...").icon(UiButton.ICON_GEAR).delay(310));
        this.buttonList.add(new UiButton(7, cx - bw / 2, y + 6 * (bh + gap) + 8, bw, bh, "Done").style(UiButton.PRIMARY).delay(360));
        sync();
    }

    private void sync() {
        bHud.on = Settings.hud;
        bPart.on = Settings.particles;
        bToast.on = Settings.toasts;
        bLoad.on = Settings.customLoading;
        bFade.displayString = "Screen fades: " + Settings.FADE_NAMES[Settings.fade];
    }

    @Override
    protected void actionPerformed(GuiButton b) throws IOException {
        switch (b.id) {
            case 1: Settings.hud = !Settings.hud; break;
            case 2: Settings.particles = !Settings.particles; break;
            case 3: Settings.toasts = !Settings.toasts; break;
            case 4: Settings.customLoading = !Settings.customLoading; break;
            case 5: Settings.fade = (Settings.fade + 1) % 4; break;
            case 6: closeTo(new GuiOptions(this, this.mc.gameSettings)); return;
            case 7: Settings.save(); closeTo(parent); return;
            default: break;
        }
        Settings.save();
        sync();
    }

    @Override
    protected void onKey(char c, int key) throws IOException {
        if (key == org.lwjgl.input.Keyboard.KEY_ESCAPE) { Settings.save(); closeTo(parent); }
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        drawBackdrop(30);
        Draw.panel(cardX, cardY, cardW, cardH, 8, Theme.GLASS, Theme.BORDER);
        Draw.centered("OPTIONS", this.width / 2f, cardY + 10, Theme.TEXT, 1.6f, true);
        Draw.centered("KB Client preferences", this.width / 2f, cardY + 26, Theme.MUTED, 0.8f, false);
        super.drawScreen(mouseX, mouseY, partialTicks);
        drawFade();
    }
}
"""
    with open(options_path, "w", encoding="utf-8") as f:
        f.write(options_code)
    print(f"Reverted: {options_path}")

    # 4. Revert Settings.java
    settings_path = os.path.join(ui_dir, "Settings.java")
    settings_code = r"""package com.oryvex.kbclient.ui;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.Properties;
import net.minecraft.client.Minecraft;

public final class Settings {
    private Settings() {}

    public static final String[] FADE_NAMES = { "Off", "Fast", "Normal", "Slow" };

    public static boolean hud = true;
    public static boolean particles = true;
    public static boolean toasts = true;
    public static boolean customLoading = true;
    public static int fade = 2;

    private static File file() {
        File dir = new File(Minecraft.getMinecraft().mcDataDir, "kbclient");
        if (!dir.exists()) dir.mkdirs();
        return new File(dir, "settings.properties");
    }

    public static void load() {
        try {
            File f = file();
            if (!f.exists()) return;
            Properties p = new Properties();
            FileInputStream in = new FileInputStream(f);
            try { p.load(in); } finally { in.close(); }
            hud = Boolean.parseBoolean(p.getProperty("hud", "true"));
            particles = Boolean.parseBoolean(p.getProperty("particles", "true"));
            toasts = Boolean.parseBoolean(p.getProperty("toasts", "true"));
            customLoading = Boolean.parseBoolean(p.getProperty("customLoading", "true"));
            fade = Math.max(0, Math.min(3, Integer.parseInt(p.getProperty("fade", "2"))));
        } catch (Throwable ignored) { }
    }

    public static void save() {
        try {
            Properties p = new Properties();
            p.setProperty("hud", String.valueOf(hud));
            p.setProperty("particles", String.valueOf(particles));
            p.setProperty("toasts", String.valueOf(toasts));
            p.setProperty("customLoading", String.valueOf(customLoading));
            p.setProperty("fade", String.valueOf(fade));
            FileOutputStream out = new FileOutputStream(file());
            try { p.store(out, "KB Client settings"); } finally { out.close(); }
        } catch (Throwable ignored) { }
    }
}
"""
    with open(settings_path, "w", encoding="utf-8") as f:
        f.write(settings_code)
    print(f"Reverted: {settings_path}")
    print("Discord RPC has been successfully removed from the project.")

if __name__ == "__main__":
    delete_rpc_files()