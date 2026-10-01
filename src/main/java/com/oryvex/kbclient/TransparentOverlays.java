package com.oryvex.kbclient;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.ChatLine;
import net.minecraft.client.gui.GuiIngame;
import net.minecraft.client.gui.GuiNewChat;
import net.minecraft.client.gui.ScaledResolution;
import net.minecraft.client.renderer.GlStateManager;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.scoreboard.Score;
import net.minecraft.scoreboard.ScoreObjective;
import net.minecraft.scoreboard.ScorePlayerTeam;
import net.minecraft.scoreboard.Scoreboard;
import net.minecraft.scoreboard.Team;
import net.minecraft.util.EnumChatFormatting;
import net.minecraft.util.MathHelper;
import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.client.event.RenderLivingEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

/**
 * Background-free scoreboard / tab / chat and (optionally) nametags.
 *
 *  - Scoreboard sidebar : GuiIngame.renderScoreboard() reimplemented without
 *                         the dark fill rectangles.
 *  - Tab list           : RenderGameOverlayEvent.Pre[PLAYER_LIST] cancelled.
 *  - Chat panel         : GuiNewChat subclass whose drawChat() skips every
 *                         Gui.drawRect() call.  The private Minecraft field
 *                         of GuiNewChat is NOT touched - our own reference
 *                         is used instead, so the class compiles cleanly.
 *  - Nametags           : RenderLivingEvent.Specials.Pre cancelled - the
 *                         vanilla black rectangle behind the name goes away.
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
                    Minecraft.class, mc, replacement,
                    "ingameGUI", "field_71456_v");

            /* Swap the chat panel for a background-free subclass. */
            try {
                GuiNewChat newChat = new BackgroundlessChat(mc);
                ObfuscationReflectionHelper.setPrivateValue(
                        GuiIngame.class, replacement, newChat,
                        "persistantChatGUI", "field_73841_b");
            } catch (Throwable t) {
                KBClientMod.logger.warn("[KBClient] chat swap failed: " + t);
            }

            MinecraftForge.EVENT_BUS.register(new OverlayHider());
            KBClientMod.logger.info("[KBClient] transparent overlays installed");
        } catch (Throwable t) {
            KBClientMod.logger.error("[KBClient] TransparentOverlays failed: " + t);
        }
    }

    /* ============================================================== */
    public static class TransparentGuiIngame extends GuiIngame {
        private final Minecraft mcRef;

        public TransparentGuiIngame(Minecraft mc) {
            super(mc);
            this.mcRef = mc;
        }

        @Override
        protected void renderScoreboard(ScoreObjective objective, ScaledResolution sr) {
            if (objective == null) return;

            Scoreboard sb = objective.getScoreboard();
            Collection<Score> all = sb.getSortedScores(objective);

            List<Score> list = new ArrayList<Score>();
            for (Score s : all) {
                String n = s.getPlayerName();
                if (n != null && !n.startsWith("#")) list.add(s);
            }
            if (list.size() > 15) {
                list = new ArrayList<Score>(list.subList(list.size() - 15, list.size()));
            }
            if (list.isEmpty()) return;

            int w = this.mcRef.fontRendererObj.getStringWidth(objective.getDisplayName());
            for (Score s : list) {
                Team t = sb.getPlayersTeam(s.getPlayerName());
                String line = ScorePlayerTeam.formatPlayerName(t, s.getPlayerName())
                            + EnumChatFormatting.RED + s.getScorePoints();
                w = Math.max(w, this.mcRef.fontRendererObj.getStringWidth(line));
            }

            int lineH  = this.mcRef.fontRendererObj.FONT_HEIGHT;
            int totalH = list.size() * lineH;
            int y0     = sr.getScaledHeight() / 2 + totalH / 3;
            int right  = sr.getScaledWidth() - 3;
            int left   = right - w;
            int xRight = right + 2;

            int j = 0;
            for (Score s : list) {
                ++j;
                Team t = sb.getPlayersTeam(s.getPlayerName());
                String name = ScorePlayerTeam.formatPlayerName(t, s.getPlayerName());
                String pts  = EnumChatFormatting.RED + "" + s.getScorePoints();
                int y = y0 - j * lineH;

                /* NO background rects here. */
                this.mcRef.fontRendererObj.drawString(name, left, y, 553648127);
                this.mcRef.fontRendererObj.drawString(
                        pts,
                        xRight - this.mcRef.fontRendererObj.getStringWidth(pts),
                        y, 553648127);

                if (j == list.size()) {
                    String title = objective.getDisplayName();
                    this.mcRef.fontRendererObj.drawString(
                            title,
                            left + w / 2
                                    - this.mcRef.fontRendererObj.getStringWidth(title) / 2,
                            y - lineH, 553648127);
                }
            }
        }
    }

    /* ============================================================== */
    /*  GuiNewChat with no dark panel behind the text                 */
    /* ============================================================== */
    public static class BackgroundlessChat extends GuiNewChat {
        private final Minecraft mcRef;
        private static Field F_LINES, F_SCROLL;

        static {
            F_LINES  = findField(GuiNewChat.class, "drawnChatLines", "field_146253_i");
            F_SCROLL = findField(GuiNewChat.class, "scrollPos",       "field_146250_j");
        }

        public BackgroundlessChat(Minecraft mc) {
            super(mc);
            this.mcRef = mc;
        }

        private static Field findField(Class<?> c, String... names) {
            for (String n : names) {
                try {
                    Field f = c.getDeclaredField(n);
                    f.setAccessible(true);
                    return f;
                } catch (Throwable ignored) { }
            }
            return null;
        }

        /* Same signature as GuiNewChat.drawChat(int); no @Override so the
         * compiler cannot complain about mapping mismatch.  At runtime this
         * still dispatches as an override if the mapping matches. */
        public void drawChat(int updateCounter) {
            if (mcRef == null || mcRef.gameSettings == null) return;
            if (mcRef.gameSettings.chatVisibility == EntityPlayer.EnumChatVisibility.HIDDEN) return;

            if (F_LINES == null || F_SCROLL == null) {
                super.drawChat(updateCounter);
                return;
            }
            try {
                @SuppressWarnings("unchecked")
                List<ChatLine> lines = (List<ChatLine>) F_LINES.get(this);
                int scrollPos = F_SCROLL.getInt(this);
                if (lines == null) return;

                int lineCount = this.getLineCount();
                boolean chatOpen = this.getChatOpen();
                int total = lines.size();
                if (total <= 0) return;

                float opacity = mcRef.gameSettings.chatOpacity * 0.9F + 0.1F;
                float scale = this.getChatScale();
                if (scale <= 0) scale = 1;

                GlStateManager.pushMatrix();
                GlStateManager.translate(2.0F, 20.0F, 0.0F);
                GlStateManager.scale(scale, scale, 1.0F);

                for (int i = 0; i + scrollPos < total && i < lineCount; i++) {
                    ChatLine cl = lines.get(i + scrollPos);
                    if (cl == null) continue;

                    int age = updateCounter - cl.getUpdatedCounter();
                    if (age >= 200 && !chatOpen) continue;

                    double d = (double) age / 200.0D;
                    d = 1.0D - d;
                    d = d * 10.0D;
                    d = MathHelper.clamp_double(d, 0.0D, 1.0D);
                    d = d * d;

                    int a = (int)(255.0D * d);
                    if (chatOpen) a = 255;
                    a = (int)((float) a * opacity);
                    if (a <= 3) continue;

                    int x = 0;
                    int y = -i * 9;

                    /* NO background rect. */

                    String s = cl.getChatComponent().getFormattedText();
                    GlStateManager.enableBlend();
                    mcRef.fontRendererObj.drawStringWithShadow(
                            s, (float) x, (float)(y - 8),
                            16777215 + (a << 24));
                    GlStateManager.disableAlpha();
                    GlStateManager.disableBlend();
                }

                GlStateManager.popMatrix();
            } catch (Throwable t) {
                try { super.drawChat(updateCounter); } catch (Throwable ignored) { }
            }
        }
    }

    /* ============================================================== */
    /*  Scoreboard / tab / nametag hider                              */
    /* ============================================================== */
    public static class OverlayHider {
        /* Tab list: hide entirely (there is no "no-background" option -
         * the list only exists as a floating panel). */
        @SubscribeEvent
        public void onOverlayPre(RenderGameOverlayEvent.Pre e) {
            if (e.type == RenderGameOverlayEvent.ElementType.PLAYER_LIST) {
                e.setCanceled(true);
            }
        }

        /* Nametags: hide the vanilla label (it has a black background). */
        @SubscribeEvent
        public void onSpecialsPre(RenderLivingEvent.Specials.Pre<EntityLivingBase> e) {
            if (e.entity instanceof EntityPlayer) {
                /* Cancel for other players only - never hide our own. */
                Minecraft mc = Minecraft.getMinecraft();
                if (e.entity != mc.thePlayer) {
                    e.setCanceled(true);
                }
            }
        }
    }
}
