package com.oryvex.kbclient;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiIngame;
import net.minecraft.client.gui.ScaledResolution;
import net.minecraft.scoreboard.Score;
import net.minecraft.scoreboard.ScoreObjective;
import net.minecraft.scoreboard.ScorePlayerTeam;
import net.minecraft.scoreboard.Scoreboard;
import net.minecraft.scoreboard.Team;
import net.minecraft.util.EnumChatFormatting;

import net.minecraftforge.client.event.RenderGameOverlayEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.ObfuscationReflectionHelper;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;

/**
 * Makes the scoreboard sidebar and the tab list background-free.
 *
 *  - Tab list    : RenderGameOverlayEvent.Pre[PLAYER_LIST] is cancelled.
 *  - Scoreboard  : GuiIngame.renderScoreboard() is re-implemented with the
 *                  dark fill rects removed; the text stays exactly the same.
 *
 * Chat transparency is intentionally NOT touched here - GuiNewChat.drawChat
 * is not a portable override across the various 1.8.9 MCP mapping snapshots
 * and its `mc` field is private, so interfering with it is unsafe without
 * bytecode manipulation.  The chat box therefore keeps its vanilla look.
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

            MinecraftForge.EVENT_BUS.register(new TabHider());
            KBClientMod.logger.info("[KBClient] transparent overlays installed");
        } catch (Throwable t) {
            KBClientMod.logger.error("[KBClient] TransparentOverlays failed: " + t);
        }
    }

    /* ============================================================= */
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

            /* width of the longest line */
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

                /* >> no background rects here, on purpose << */
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

    /* ============================================================= */
    public static class TabHider {
        @SubscribeEvent
        public void onRenderPre(RenderGameOverlayEvent.Pre e) {
            if (e.type == RenderGameOverlayEvent.ElementType.PLAYER_LIST) {
                e.setCanceled(true);
            }
        }
    }
}
