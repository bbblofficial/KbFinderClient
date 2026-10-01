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
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.scoreboard.Score;
import net.minecraft.scoreboard.ScoreObjective;
import net.minecraft.scoreboard.ScorePlayerTeam;
import net.minecraft.scoreboard.Scoreboard;
import net.minecraft.scoreboard.Team;
import net.minecraft.util.EnumChatFormatting;
import net.minecraft.util.MathHelper;

import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

/**
 * Makes the scoreboard / tab list / chat backgrounds fully transparent
 * WITHOUT removing any text content.
 *
 *  - Tab list     : RenderGameOverlayEvent.Pre PLAYER_LIST is cancelled
 *  - Scoreboard   : GuiIngame.renderScoreboard() re-implemented with no fill
 *  - Chat         : GuiNewChat.drawChat() re-implemented with no fill
 *
 * Everything is 1.8.9 (stable_22) safe:
 *   - uses ScoreObjective / Team / ScorePlayerTeam  (NOT the 1.10+ names)
 *   - uses plain java.lang.reflect.Field for the GuiNewChat privates
 *     (ObfuscationReflectionHelper.findField does not exist on 1.8.9)
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

    /* ============================================================== */
    /*  GuiIngame subclass - scoreboard / player-list overrides        */
    /* ============================================================== */
    public static class TransparentGuiIngame extends GuiIngame {
        public TransparentGuiIngame(Minecraft mc) { super(mc); }

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

            int w = this.mc.fontRendererObj.getStringWidth(objective.getDisplayName());
            for (Score s : list) {
                Team t = sb.getPlayersTeam(s.getPlayerName());
                String s1 = ScorePlayerTeam.formatPlayerName(t, s.getPlayerName());
                String s2 = EnumChatFormatting.RED + "" + s.getScorePoints();
                w = Math.max(w, this.mc.fontRendererObj.getStringWidth(s1 + s2));
            }

            int lineH  = this.mc.fontRendererObj.FONT_HEIGHT;
            int totalH = list.size() * lineH;
            int y0     = sr.getScaledHeight() / 2 + totalH / 3;
            int right  = sr.getScaledWidth() - 3;
            int left   = right - w;
            int xRight = right + 2;

            int j = 0;
            for (Score s : list) {
                ++j;
                Team t = sb.getPlayersTeam(s.getPlayerName());
                String s1 = ScorePlayerTeam.formatPlayerName(t, s.getPlayerName());
                String s2 = EnumChatFormatting.RED + "" + s.getScorePoints();
                int y = y0 - j * lineH;

                /* >>> background rects REMOVED on purpose <<< */
                this.mc.fontRendererObj.drawString(s1, left, y, 553648127);
                this.mc.fontRendererObj.drawString(s2,
                        xRight - this.mc.fontRendererObj.getStringWidth(s2), y, 553648127);

                if (j == list.size()) {
                    String title = objective.getDisplayName();
                    this.mc.fontRendererObj.drawString(title,
                            left + w / 2
                                    - this.mc.fontRendererObj.getStringWidth(title) / 2,
                            y - lineH, 553648127);
                }
            }
        }

        @Override
        protected void renderPlayerList(ScaledResolution sr, Scoreboard sb) {
            /* no-op - TabHider already cancels the event, this is the belt */
        }
    }

    /* ============================================================== */
    /*  GuiNewChat subclass - chat without the dark background         */
    /* ============================================================== */
    public static class TransparentChat extends GuiNewChat {
        private static final Field F_LINES  = findField(GuiNewChat.class,
                "drawnChatLines", "field_146253_i");
        private static final Field F_SCROLL = findField(GuiNewChat.class,
                "scrollPos", "field_146250_j");

        public TransparentChat(Minecraft mc) { super(mc); }

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

        @Override
        public void drawChat(int updateCounter) {
            if (this.mc.gameSettings.chatVisibility == EntityPlayer.EnumChatVisibility.HIDDEN) return;
            if (F_LINES == null || F_SCROLL == null) {
                super.drawChat(updateCounter);
                return;
            }
            try {
                @SuppressWarnings("unchecked")
                List<ChatLine> lines = (List<ChatLine>) F_LINES.get(this);
                int scrollPos = F_SCROLL.getInt(this);
                if (lines == null) return;

                int  lineCount = this.getLineCount();
                boolean chatOpen = this.getChatOpen();
                int  total = lines.size();
                if (total <= 0) return;

                float opacity = this.mc.gameSettings.chatOpacity * 0.9F + 0.1F;
                float scale   = this.getChatScale();
                int   boxW    = MathHelper.ceiling_float_int(this.getChatWidth() / scale);
                if (boxW < 1) boxW = 1;

                GlStateManager.pushMatrix();
                GlStateManager.translate(2.0F, 20.0F, 0.0F);
                GlStateManager.scale(scale, scale, 1.0F);

                for (int i = 0; i + scrollPos < total && i < lineCount; i++) {
                    ChatLine cl = lines.get(i + scrollPos);
                    if (cl == null) continue;

                    int age = updateCounter - cl.getUpdatedCounter();
                    if (age >= 200 && !chatOpen) continue;

                    double d0 = (double) age / 200.0D;
                    d0 = 1.0D - d0;
                    d0 = d0 * 10.0D;
                    d0 = MathHelper.clamp_double(d0, 0.0D, 1.0D);
                    d0 = d0 * d0;

                    int a = (int)(255.0D * d0);
                    if (chatOpen) a = 255;
                    a = (int)((float) a * opacity);
                    if (a <= 3) continue;

                    int x = 0;
                    int y = -i * 9;

                    /* >>> background rects REMOVED on purpose <<< */

                    String s = cl.getChatComponent().getFormattedText();
                    GlStateManager.enableBlend();
                    this.mc.fontRendererObj.drawStringWithShadow(
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
    /*  Tab list canceller                                             */
    /* ============================================================== */
    public static class TabHider {
        @SubscribeEvent
        public void onRenderPre(RenderGameOverlayEvent.Pre e) {
            if (e.type == RenderGameOverlayEvent.ElementType.PLAYER_LIST) {
                e.setCanceled(true);
            }
        }
    }
}
