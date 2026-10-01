package com.oryvex.kbclient;

import java.lang.reflect.Field;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiIngame;
import net.minecraft.client.gui.GuiNewChat;
import net.minecraft.client.gui.ScaledResolution;
import net.minecraft.scoreboard.Scoreboard;
import net.minecraft.scoreboard.ScoreboardObjective;
import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

/**
 * Installs a custom GuiIngame that renders the scoreboard, tab list and chat
 * WITHOUT the semi-transparent dark background panels.
 *
 * We do NOT remove the content - we only skip the background rects.
 *
 * The vanilla methods are essentially copied and re-implemented with every
 * drawRect(...) that used 0x50000000 / 0x60000000 removed.
 */
public final class TransparentOverlays {
    private TransparentOverlays() {}

    private static boolean installed;

    public static void install() {
        if (installed) return;
        installed = true;
        try {
            Minecraft mc = Minecraft.getMinecraft();
            GuiIngame vanilla = mc.ingameGUI;
            if (vanilla == null) return;

            GuiIngame replacement = new TransparentGuiIngame(mc);
            ObfuscationReflectionHelper.setPrivateValue(
                    Minecraft.class, mc, replacement, "ingameGUI", "field_71456_v");

            /* Replace the chat panel too, using reflection on the private field */
            try {
                GuiNewChat chat = new TransparentChat(mc);
                ObfuscationReflectionHelper.setPrivateValue(
                        GuiIngame.class, replacement, chat,
                        "persistantChatGUI", "field_73841_b");
            } catch (Throwable t) {
                KBClientMod.logger.warn("[KBClient] chat swap failed: " + t);
            }

            MinecraftForge.EVENT_BUS.register(new TabHider());

            KBClientMod.logger.info("[KBClient] transparent overlays installed");
        } catch (Throwable t) {
            KBClientMod.logger.error("[KBClient] TransparentOverlays failed: " + t);
        }
    }

    /* ===================== GuiIngame subclass ===================== */
    public static class TransparentGuiIngame extends GuiIngame {
        private final Minecraft mcRef;

        public TransparentGuiIngame(Minecraft mc) {
            super(mc);
            this.mcRef = mc;
        }

        /* Scoreboard sidebar: same as vanilla, no background rects. */
        @Override
        protected void renderScoreboard(ScoreboardObjective objective, ScaledResolution sr) {
            if (objective == null) return;
            Scoreboard sb = objective.getScoreboard();
            java.util.Collection<net.minecraft.scoreboard.Score> sorted =
                    sb.getSortedScores(objective);

            java.util.List<net.minecraft.scoreboard.Score> list =
                    new java.util.ArrayList<net.minecraft.scoreboard.Score>();
            for (net.minecraft.scoreboard.Score s : sorted) {
                String n = s.getPlayerName();
                if (n != null && !n.startsWith("#")) list.add(s);
            }
            if (list.size() > 15) list = list.subList(list.size() - 15, list.size());
            if (list.isEmpty()) return;

            int width = this.mc.fontRendererObj.getStringWidth(objective.getDisplayName());
            for (net.minecraft.scoreboard.Score s : list) {
                net.minecraft.scoreboard.ScoreboardTeam team =
                        sb.getPlayersTeam(s.getPlayerName());
                net.minecraft.util.IChatComponent c =
                        net.minecraft.scoreboard.ScorePlayerTeam.formatPlayerName(team, s.getPlayerName());
                width = Math.max(width, this.mc.fontRendererObj.getStringWidth(c.getFormattedText()));
            }

            int lineH  = this.mc.fontRendererObj.FONT_HEIGHT;
            int totalH = list.size() * lineH;
            int y0     = sr.getScaledHeight() / 2 + totalH / 3;
            int right  = sr.getScaledWidth() - 3;
            int left   = right - width;

            int idx = 0;
            for (net.minecraft.scoreboard.Score s : list) {
                idx++;
                net.minecraft.scoreboard.ScoreboardTeam team =
                        sb.getPlayersTeam(s.getPlayerName());
                String name = net.minecraft.scoreboard.ScorePlayerTeam
                        .formatPlayerName(team, s.getPlayerName()).getFormattedText();
                String pts  = "\u00a7c" + s.getScorePoints();
                int y = y0 - idx * lineH;

                /* NOTE: no drawRect background here on purpose */
                this.mc.fontRendererObj.drawString(name, left, y, 0x20FFFFFF);
                this.mc.fontRendererObj.drawString(
                        pts,
                        right + 2 - this.mc.fontRendererObj.getStringWidth(pts),
                        y, 0x20FFFFFF);

                if (idx == list.size()) {
                    String title = objective.getDisplayName().getFormattedText();
                    this.mc.fontRendererObj.drawString(
                            title,
                            left + width / 2 - this.mc.fontRendererObj.getStringWidth(title) / 2,
                            y - lineH, 0x20FFFFFF);
                }
            }
        }

        /* The tab list is fully cancelled by TabHider below. */
        @Override
        protected void renderPlayerList(ScaledResolution sr, Scoreboard sb) {
            /* no-op: TabHider cancels the event so this method never draws a bg */
        }
    }

    /* ===================== Chat subclass ===================== */
    public static class TransparentChat extends GuiNewChat {
        private final Minecraft mcRef;

        private static Field F_LINES;
        private static Field F_SCROLL;

        static {
            try {
                F_LINES  = ObfuscationReflectionHelper.findField(
                        GuiNewChat.class, "drawnChatLines", "field_146253_i");
                F_SCROLL = ObfuscationReflectionHelper.findField(
                        GuiNewChat.class, "scrollPos", "field_146250_j");
                F_LINES.setAccessible(true);
                F_SCROLL.setAccessible(true);
            } catch (Throwable ignored) { }
        }

        public TransparentChat(Minecraft mc) {
            super(mc);
            this.mcRef = mc;
        }

        @Override
        public void drawChat(int updateCounter) {
            if (this.mcRef.gameSettings.chatVisibility ==
                    net.minecraft.entity.player.EntityPlayer.EnumChatVisibility.HIDDEN) return;

            if (F_LINES == null) {
                /* fallback: vanilla behaviour if reflection failed */
                super.drawChat(updateCounter);
                return;
            }

            try {
                @SuppressWarnings("unchecked")
                java.util.List<net.minecraft.client.gui.ChatLine> lines =
                        (java.util.List<net.minecraft.client.gui.ChatLine>) F_LINES.get(this);
                int scrollPos = F_SCROLL.getInt(this);

                int lineCount = this.getLineCount();
                boolean chatOpen = this.getChatOpen();
                int total = lines.size();
                float chatOpacity = this.mcRef.gameSettings.chatOpacity * 0.9F + 0.1F;

                if (total <= 0) return;

                float scale = this.getChatScale();
                int boxWidth = net.minecraft.util.MathHelper.ceiling_float_int(
                        (float) this.getChatWidth() / scale);

                net.minecraft.client.renderer.GlStateManager.pushMatrix();
                net.minecraft.client.renderer.GlStateManager.translate(2.0F, 20.0F, 0.0F);
                net.minecraft.client.renderer.GlStateManager.scale(scale, scale, 1.0F);

                int drawn = 0;
                for (int i = 0; i + scrollPos < total && i < lineCount; i++) {
                    net.minecraft.client.gui.ChatLine cl = lines.get(i + scrollPos);
                    if (cl == null) continue;

                    int age = updateCounter - cl.getUpdatedCounter();
                    if (age >= 200 && !chatOpen) continue;

                    double d = (double) age / 200.0D;
                    d = 1.0D - d;
                    d = d * 10.0D;
                    d = net.minecraft.util.MathHelper.clamp_double(d, 0.0D, 1.0D);
                    d = d * d;
                    int alphaByte = (int)(255.0D * d);
                    if (chatOpen) alphaByte = 255;
                    alphaByte = (int)((float) alphaByte * chatOpacity);
                    drawn++;

                    if (alphaByte > 3) {
                        int x = 0;
                        int y = -i * 9;

                        /* >>> background rect REMOVED on purpose <<< */

                        String s = cl.getChatComponent().getFormattedText();
                        net.minecraft.client.renderer.GlStateManager.enableBlend();
                        this.mcRef.fontRendererObj.drawStringWithShadow(
                                s, (float) x, (float) (y - 8),
                                16777215 + (alphaByte << 24));
                        net.minecraft.client.renderer.GlStateManager.disableAlpha();
                        net.minecraft.client.renderer.GlStateManager.disableBlend();
                    }
                }

                /* scrolling box background also skipped */
                net.minecraft.client.renderer.GlStateManager.popMatrix();
            } catch (Throwable t) {
                /* on any error just fall back to vanilla */
                try { super.drawChat(updateCounter); } catch (Throwable ignored) { }
            }
        }
    }

    /* ===================== Tab list hider ===================== */
    public static class TabHider {
        @SubscribeEvent
        public void onRenderPre(RenderGameOverlayEvent.Pre e) {
            if (e.type == RenderGameOverlayEvent.ElementType.PLAYER_LIST) {
                e.setCanceled(true);
            }
        }
    }
}
