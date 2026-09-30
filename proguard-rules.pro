-dontshrink
-dontoptimize
-keepattributes *Annotation*,Signature,Exceptions,InnerClasses,EnclosingMethod

# Prevent build failures from unreferenced Minecraft/Forge classes
-dontwarn net.minecraft.**
-dontwarn net.minecraftforge.**
-dontwarn org.apache.**
-dontwarn com.google.**
-dontwarn io.netty.**
-dontwarn org.lwjgl.**
-dontwarn club.minnced.**

# Keep Forge mod entry points and event handlers intact for reflection
-keep @net.minecraftforge.fml.common.Mod class * { *; }
-keepclassmembers class * {
    @net.minecraftforge.fml.common.eventhandler.SubscribeEvent *;
    @net.minecraftforge.fml.common.Mod$EventHandler *;
}

# Protect the mod's core functionality and UI from being mangled
-keep class com.oryvex.kbclient.** { *; }
