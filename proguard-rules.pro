-dontshrink
-dontoptimize
-ignorewarnings
-dontwarn **

-keepattributes *Annotation*,Signature,Exceptions,InnerClasses,EnclosingMethod

# Keep Forge mod entry points and event handlers intact for reflection
-keep @net.minecraftforge.fml.common.Mod class * { *; }
-keepclassmembers class * {
    @net.minecraftforge.fml.common.eventhandler.SubscribeEvent *;
    @net.minecraftforge.fml.common.Mod$EventHandler *;
}

# Protect the mod's core functionality and UI from being mangled
-keep class com.oryvex.kbclient.** { *; }