# ProGuard rules for KB Client (Forge 1.8.9 client mod)
# Run against the built mod jar only (Minecraft/Forge/Netty classes are not
# reprocessed - they're just referenced, so warnings about them are expected).

-dontoptimize
-dontpreverify
-dontwarn **
-ignorewarnings

-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

# Forge finds the mod entry point by its @Mod annotation and calls its
# @EventHandler lifecycle methods by reflection - both must survive.
-keep @net.minecraftforge.fml.common.Mod class * {
    @net.minecraftforge.fml.common.Mod$EventHandler <methods>;
}

# Forge's event bus finds listeners by @SubscribeEvent via reflection.
-keepclassmembers class * {
    @net.minecraftforge.fml.common.eventhandler.SubscribeEvent <methods>;
}

# Registered client command - keep its identity/usage strings and dispatch.
-keep class com.oryvex.kbclient.KBCommand { *; }

# Keep enum semantics (values()/valueOf() are used reflectively by libraries).
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}