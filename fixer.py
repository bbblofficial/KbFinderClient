import os
import subprocess

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated: {os.path.basename(path)}")

base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, "src", "main", "java", "com", "oryvex", "kbclient")
ui_dir = os.path.join(src_dir, "ui")

# 1. Fix Draw.java (Add missing static methods)
draw_content = """package com.oryvex.kbclient.ui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.renderer.GlStateManager;
import java.util.ArrayList;
import java.util.List;

/** Minimal immediate-mode drawing toolkit. */
public final class Draw {
    private Draw() {}

    public static float clamp(float v) { return v < 0f ? 0f : (v > 1f ? 1f : v); }
    
    public static float ease(float t) {
        t = clamp(t);
        return t * t * (3f - 2f * t);
    }

    public static float easeOut(float t) {
        t = clamp(t);
        float u = 1f - t;
        return 1f - u * u * u;
    }

    public static int lerp(int a, int b, float t) {
        t = clamp(t);
        int aa = (a >>> 24) & 255, ar = (a >> 16) & 255, ag = (a >> 8) & 255, ab = a & 255;
        int ba = (b >>> 24) & 255, br = (b >> 16) & 255, bg = (b >> 8) & 255, bb = b & 255;
        return (((int)(aa + (ba - aa) * t)) << 24) | (((int)(ar + (br - ar) * t)) << 16) | (((int)(ag + (bg - ag) * t)) << 8) | ((int)(ab + (bb - ab) * t));
    }

    public static int alpha(int color, float a) { return ((int)(clamp(a) * 255f) << 24) | (color & 0xFFFFFF); }
    public static int fade(int color, float a) { return ((int)(((color >>> 24) & 255) * clamp(a)) << 24) | (color & 0xFFFFFF); }

    public static int confColor(double c) {
        float f = (float) Math.max(0, Math.min(1, c));
        return f < 0.5f ? lerp(Theme.BAD, Theme.WARN, f * 2f) : lerp(Theme.WARN, Theme.GOOD, (f - 0.5f) * 2f);
    }

    public static void blend() {
        GlStateManager.enableBlend();
        GlStateManager.tryBlendFuncSeparate(770, 771, 1, 0);
        GlStateManager.color(1f, 1f, 1f, 1f);
    }

    public static void resetColor() {
        GlStateManager.color(1f, 1f, 1f, 1f);
        GlStateManager.disableBlend();
    }

    public static void rect(float x, float y, float w, float h, int color) {
        Gui.drawRect((int) x, (int) y, (int)(x + w), (int)(y + h), color);
    }

    public static void roundRect(float x, float y, float w, float h, float r, int color) {
        if (w <= 0f || h <= 0f) return;
        if (((color >>> 24) & 255) <= 4) return;
        r = Math.min(r, Math.min(w, h) / 2f);
        int ir = (int) Math.ceil(r);
        if (ir <= 0) { Gui.drawRect((int) x, (int) y, (int)(x + w), (int)(y + h), color); return; }
        Gui.drawRect((int) x, (int)(y + r), (int)(x + w), (int)(y + h - r), color);
        Gui.drawRect((int)(x + r), (int) y, (int)(x + w - r), (int)(y + r), color);
        Gui.drawRect((int)(x + r), (int)(y + h - r), (int)(x + w - r), (int)(y + h), color);
        for (int i = 0; i < ir; i++) {
            double dy = ir - i - 0.5;
            int inset = (int) Math.round(ir - Math.sqrt(Math.max(0, ir * ir - dy * dy)));
            Gui.drawRect((int)(x + inset), (int)(y + i), (int)(x + w - inset), (int)(y + i + 1), color);
            Gui.drawRect((int)(x + inset), (int)(y + h - i - 1), (int)(x + w - inset), (int)(y + h - i), color);
        }
    }

    public static void roundOutline(float x, float y, float w, float h, float r, float t, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        rect(x + r, y, w - 2 * r, t, color);
        rect(x + r, y + h - t, w - 2 * r, t, color);
        rect(x, y + r, t, h - 2 * r, color);
        rect(x + w - t, y + r, t, h - 2 * r, color);
    }

    public static void panel(float x, float y, float w, float h, float r, int fill, int border) {
        if (((fill >>> 24) & 255) > 4) roundRect(x, y, w, h, r, fill);
        if (border != 0 && ((border >>> 24) & 255) > 4) roundOutline(x, y, w, h, r, 1f, border);
    }

    public static void bar(float x, float y, float w, float h, double frac, int bg, int fg) {
        roundRect(x, y, w, h, h / 2f, bg);
        float fw = (float)(w * Math.max(0, Math.min(1, frac)));
        if (fw > 0f) roundRect(x, y, fw, h, h / 2f, fg);
    }

    public static void circle(float cx, float cy, float r, int color) {
        if (((color >>> 24) & 255) <= 4) return;
        int ir = (int) Math.ceil(r);
        for (int dy = -ir; dy <= ir; dy++) {
            int half = (int) Math.sqrt(Math.max(0, ir * ir - dy * dy));
            rect(cx - half, cy + dy, half * 2, 1, color);
        }
    }

    public static void dashedH(float x, float y, float w, int color) {
        if (w <= 0f || ((color >>> 24) & 255) <= 4) return;
        for (float i = 0f; i < w; i += 6f) {
            int x0 = (int)(x + i);
            int x1 = (int)(x + Math.min(w, i + 3f));
            Gui.drawRect(x0, (int) y, x1, (int) y + 1, color);
        }
    }

    public static FontRenderer font() {
        try {
            com.oryvex.kbclient.font.ModernFontRenderer mf = com.oryvex.kbclient.KBClientMod.modernFont;
            if (mf != null) return mf;
        } catch (Throwable ignored) { }
        return Minecraft.getMinecraft().fontRendererObj;
    }

    public static int width(String s, float scale) { return (int)(font().getStringWidth(s) * scale); }
    public static int w(String s, float scale, boolean bold) { return width(s, scale); }
    public static float lineH(float scale) { return font().FONT_HEIGHT * scale; }

    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, shadow);
        GlStateManager.popMatrix();
    }

    public static void centered(String s, float cx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, cx - tw / 2f, cy - th / 2f, color, scale, shadow);
    }

    public static void left(String s, float x, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float th = font().FONT_HEIGHT * scale;
        text(s, x, cy - th / 2f, color, scale, shadow);
    }

    public static void right(String s, float rx, float cy, int color, float scale, boolean shadow) {
        if (s == null || s.isEmpty()) return;
        float tw = font().getStringWidth(s) * scale;
        float th = font().FONT_HEIGHT * scale;
        text(s, rx - tw, cy - th / 2f, color, scale, shadow);
    }

    public static String fit(String s, float maxW, float scale, boolean bold) {
        if (s == null) return "";
        if (w(s, scale, bold) <= maxW) return s;
        String ell = "...";
        while (s.length() > 0 && w(s + ell, scale, bold) > maxW) {
            s = s.substring(0, s.length() - 1);
        }
        return s + ell;
    }
}
"""
write_file(os.path.join(ui_dir, "Draw.java"), draw_content)

# 2. Fix KBClientMod.java (Update capture call to include old motion)
mod_content = """package com.oryvex.kbclient;

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
    public static final String VERSION = "1.0.0";
    private static final String HOOK = "kb_client_handler";
    private static KBClientMod instance;
    public static Logger logger;
    public static com.oryvex.kbclient.font.ModernFontRenderer modernFont;
    private final KBTracker tracker = new KBTracker();
    private KeyBinding openKey;
    private Channel hookedChannel;
    private boolean pendingOpen;
    private Object lastWorld;
    public static net.minecraft.client.multiplayer.ServerData lastServerData;
    public static KBLoading customLoadingScreen;

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
        MinecraftForge.EVENT_BUS.register(__fix);
        net.minecraftforge.fml.common.FMLCommonHandler.instance().bus().register(__fix);
        MinecraftForge.EVENT_BUS.register(this);
        ClientCommandHandler.instance.registerCommand(new KBCommand());
        openKey = new KeyBinding("Open KB Analyzer", Keyboard.KEY_RSHIFT, "KB Client");
        ClientRegistry.registerKeyBinding(openKey);
        installLoading();
        
        try {
            Minecraft mcF = Minecraft.getMinecraft();
            modernFont = new com.oryvex.kbclient.font.ModernFontRenderer(
                mcF.gameSettings,
                new net.minecraft.util.ResourceLocation("textures/font/ascii.png"),
                mcF.renderEngine, false
            );
            logger.info("[KBClient] ModernFontRenderer loaded");
        } catch (Throwable t) {
            logger.error("[KBClient] ModernFontRenderer failed: " + t);
        }
        
        DiscordRPC.start();
    }

    private void installLoading() {
        final Minecraft mc = Minecraft.getMinecraft();
        customLoadingScreen = new KBLoading(mc);
        try {
            ObfuscationReflectionHelper.setPrivateValue(Minecraft.class, mc, customLoadingScreen, "loadingScreen", "field_71461_s");
            logger.info("[KBClient] custom loading screen installed");
            
            Thread loadingThemer = new Thread(new Runnable() {
                @Override
                public void run() {
                    while (true) {
                        try { Thread.sleep(2); } catch (Exception ignored) {}
                        if (Settings.customLoading && mc.loadingScreen != null && mc.loadingScreen != customLoadingScreen) {
                            try {
                                ObfuscationReflectionHelper.setPrivateValue(Minecraft.class, mc, customLoadingScreen, "loadingScreen", "field_71461_s");
                            } catch (Exception ignored) {}
                        }
                    }
                }
            }, "KBClient-LoadingThemer");
            loadingThemer.setDaemon(true);
            loadingThemer.start();
        } catch (Throwable t) {
            logger.error("[KBClient] could not install loading screen: " + t);
        }
    }

    @SubscribeEvent
    public void onGuiOpen(GuiOpenEvent e) {
        Minecraft mc = Minecraft.getMinecraft();
        if (e.gui instanceof GuiMainMenu) {
            e.gui = new GuiModernMenu(tracker);
        }
        if (e.gui == null) {
            if (mc.theWorld != null && !(mc.currentScreen instanceof GuiChat) && !(mc.currentScreen instanceof GuiContainer)) {
                Fade.world.trigger(0.45f);
            }
        } else if (!(e.gui instanceof FadeScreen) && !(e.gui instanceof GuiChat)) {
            Fade.screen.trigger(e.gui instanceof GuiContainer ? 0.35f : 0.75f);
        }
    }

    @SubscribeEvent
    public void onDrawScreenPre(GuiScreenEvent.DrawScreenEvent.Pre e) {
        GuiScreen g = e.gui;
        if (g == null) return;
        if (Settings.customLoading) {
            if (g instanceof net.minecraft.client.multiplayer.GuiConnecting) {
                e.setCanceled(true);
                LoadingArt.draw(g.width, g.height, "Connecting", "Joining server...", -1);
                Fade.screen.draw(g.width, g.height);
            } else if (g instanceof GuiDownloadTerrain) {
                e.setCanceled(true);
                LoadingArt.draw(g.width, g.height, "Joining world", "Downloading terrain...", -1);
                Fade.screen.draw(g.width, g.height);
            }
        }
    }

    @SubscribeEvent
    public void onDrawScreenPost(GuiScreenEvent.DrawScreenEvent.Post e) {
        GuiScreen g = e.gui;
        if (g == null || g instanceof FadeScreen) return;
        if (Settings.customLoading && (g instanceof net.minecraft.client.multiplayer.GuiConnecting || g instanceof GuiDownloadTerrain)) {
            return;
        }
        Fade.screen.draw(g.width, g.height);
    }

    @SubscribeEvent
    public void onInitGui(GuiScreenEvent.InitGuiEvent.Post e) {
        if (e.gui instanceof GuiIngameMenu) {
            for (int i = 0; i < e.buttonList.size(); i++) {
                GuiButton b = e.buttonList.get(i);
                if (b.id == 0) {
                    UiButton u = new UiButton(0, b.xPosition, b.yPosition, b.width, b.height, b.displayString);
                    u.icon = UiButton.ICON_GEAR;
                    e.buttonList.set(i, u);
                }
            }
        } else if (e.gui instanceof net.minecraft.client.gui.GuiDisconnected) {
            for (GuiButton b : e.buttonList) {
                if (b.id == 0) {
                    e.buttonList.add(new UiButton(999, b.xPosition, b.yPosition + b.height + 6, b.width, b.height, "Reconnect").style(UiButton.PRIMARY));
                    break;
                }
            }
        }
    }

    @SubscribeEvent
    public void onActionPerformed(net.minecraftforge.client.event.GuiScreenEvent.ActionPerformedEvent.Pre e) {
        if (e.gui instanceof GuiIngameMenu && e.button.id == 0) {
            e.setCanceled(true);
            Minecraft.getMinecraft().displayGuiScreen(new com.oryvex.kbclient.ui.GuiKbOptions(tracker, e.gui));
        } else if (e.gui instanceof net.minecraft.client.gui.GuiDisconnected && e.button.id == 999) {
            if (lastServerData != null) {
                Minecraft mc = Minecraft.getMinecraft();
                mc.displayGuiScreen(new net.minecraft.client.multiplayer.GuiConnecting(new GuiModernMenu(tracker), mc, lastServerData));
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
                
                // Capture OLD motion BEFORE the packet is applied
                final double oldX, oldY, oldZ;
                final boolean oldGround, oldSprint;
                if (mc.thePlayer != null && mc.thePlayer.getEntityId() == id) {
                    oldX = mc.thePlayer.motionX;
                    oldY = mc.thePlayer.motionY;
                    oldZ = mc.thePlayer.motionZ;
                    oldGround = mc.thePlayer.onGround;
                    oldSprint = mc.thePlayer.isSprinting();
                } else {
                    oldX = oldY = oldZ = 0;
                    oldGround = false;
                    oldSprint = false;
                }

                mc.addScheduledTask(new Runnable() {
                    @Override
                    public void run() {
                        EntityPlayerSP p = mc.thePlayer;
                        if (p != null && p.getEntityId() == id) {
                            // Pass all 8 arguments for high-precision extraction
                            KBClientMod.getInstance().getTracker().capture(x, y, z, oldX, oldY, oldZ, oldGround, oldSprint);
                        }
                    }
                });
            }
            super.channelRead(ctx, msg);
        }
    }
}
"""
write_file(os.path.join(src_dir, "KBClientMod.java"), mod_content)

print("\n🚀 Committing and pushing fixes to GitHub...")
try:
    subprocess.run(["git", "add", "src/main/java/com/oryvex/kbclient/KBClientMod.java", "src/main/java/com/oryvex/kbclient/ui/Draw.java"], check=True)
    subprocess.run(["git", "commit", "-m", "fix: add missing Draw methods and update capture call for precision"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✅ Successfully committed and pushed!")
except subprocess.CalledProcessError as e:
    print(f"⚠️ Git command failed: {e}")
    print("Please manually run: git add . && git commit -m 'fix build' && git push")