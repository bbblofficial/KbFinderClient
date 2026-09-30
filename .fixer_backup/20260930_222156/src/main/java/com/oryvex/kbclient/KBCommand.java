package com.oryvex.kbclient;

import com.oryvex.kbclient.kb.KBProfile;
import com.oryvex.kbclient.kb.KBYaml;
import com.oryvex.kbclient.ui.GuiAnalyzer;
import com.oryvex.kbclient.ui.Settings;
import com.oryvex.kbclient.ui.Theme;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.command.CommandBase;
import net.minecraft.command.ICommandSender;
import net.minecraft.util.BlockPos;

public class KBCommand extends CommandBase {
    @Override
    public String getCommandName() { return "kb"; }

    @Override
    public List<String> getCommandAliases() { return Arrays.asList("findkb", "kbgui"); }

    @Override
    public String getCommandUsage(ICommandSender sender) {
        return "/kb [gui | start <hits> | stop | resume | reset | export | hud | status | yaml | import [file] | sample | clear]";
    }

    @Override
    public boolean canCommandSenderUseCommand(ICommandSender sender) { return true; }

    @Override
    public int getRequiredPermissionLevel() { return 0; }

    @Override
    public void processCommand(ICommandSender sender, String[] args) {
        KBClientMod mod = KBClientMod.getInstance();
        KBTracker t = mod.getTracker();
        String a = args.length > 0 ? args[0].toLowerCase(Locale.ROOT) : "gui";

        if (a.matches("\\d+")) { t.startGoal(Integer.parseInt(a)); return; }
        if (a.equals("start")) {
            int n = 10;
            if (args.length > 1) { try { n = Integer.parseInt(args[1]); } catch (NumberFormatException ignored) { } }
            t.startGoal(n);
        } else if (a.equals("stop")) {
            t.setRecording(false);
            t.chat(Theme.S + "e[KB] recording paused");
        } else if (a.equals("resume")) {
            t.setRecording(true);
            t.chat(Theme.S + "a[KB] recording resumed");
        } else if (a.equals("reset")) {
            t.reset();
            t.chat(Theme.S + "e[KB] samples cleared");
        } else if (a.equals("export")) {
            try { t.chat(Theme.S + "a[KB] saved " + t.export().getAbsolutePath()); }
            catch (Exception e) { t.chat(Theme.S + "c[KB] export failed: " + e.getMessage()); }
        } else if (a.equals("hud")) {
            Settings.hud = !Settings.hud;
            Settings.save();
            t.chat(Theme.S + "b[KB] HUD " + (Settings.hud ? "on" : "off"));
        } else if (a.equals("yaml")) {
            GuiScreen.setClipboardString(t.getProfile().toYaml());
            t.chat(Theme.S + "a[KB] YAML copied to clipboard");
        } else if (a.equals("status")) {
            KBProfile p = t.getProfile();
            t.chat(Theme.S + "b[KB] " + Theme.S + "7" + p.used + "/" + p.total + " samples | " + p.summary());
        } else if (a.equals("sample")) {
            t.importYaml(KBYaml.SAMPLE);
            GuiAnalyzer.openTab(4);
            mod.requestOpenAnalyzer();
        } else if (a.equals("clear")) {
            t.clearReference();
            t.chat(Theme.S + "e[KB] reference cleared");
        } else if (a.equals("import")) {
            try {
                String text;
                if (args.length > 1) {
                    File f = new File(new File(Minecraft.getMinecraft().mcDataDir, "kbclient"), args[1]);
                    if (!f.exists() && !args[1].contains(".")) f = new File(f.getPath() + ".yml");
                    text = new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
                } else {
                    text = GuiScreen.getClipboardString();
                }
                KBYaml.Result r = t.importYaml(text);
                if (r.parsed > 0) { GuiAnalyzer.openTab(4); mod.requestOpenAnalyzer(); }
            } catch (Exception e) {
                t.chat(Theme.S + "c[KB] import failed: " + e.getMessage());
            }
        } else {
            mod.requestOpenAnalyzer();
        }
    }

    @Override
    public List<String> addTabCompletionOptions(ICommandSender sender, String[] args, BlockPos pos) {
        if (args.length == 1) return getListOfStringsMatchingLastWord(args, "gui", "start", "stop", "resume", "reset", "export", "hud", "status", "yaml", "import", "sample", "clear");
        if (args.length == 2 && args[0].equalsIgnoreCase("start")) return getListOfStringsMatchingLastWord(args, "5", "10", "15", "20", "30");
        return null;
    }
}
