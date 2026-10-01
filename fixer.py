import os
import re

def fix_particle_errors():
    print("🛠️️ Fixing missing particles() method by migrating to Premium Plexus Background...")

    # 1. Patch FadeScreen.java
    fadescreen_path = "src/main/java/com/oryvex/kbclient/ui/FadeScreen.java"
    if os.path.exists(fadescreen_path):
        with open(fadescreen_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # جایگزینی فراخوانی پارتیکل‌های قدیمی با افکت Plexus جدید
        content = re.sub(
            r'Draw\.particles\(this\.width,\s*this\.height,\s*particleCount,\s*0x[0-9A-Fa-f]+,\s*[0-9.]+f\);',
            r'Draw.plexusBackground(this.width, this.height, 0.35f);',
            content
        )
        
        with open(fadescreen_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Patched FadeScreen.java")
    else:
        print("❌ FadeScreen.java not found!")

    # 2. Patch LoadingArt.java
    loadingart_path = "src/main/java/com/oryvex/kbclient/ui/LoadingArt.java"
    if os.path.exists(loadingart_path):
        with open(loadingart_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # پاک کردن خط دوم پارتیکل‌ها
        content = re.sub(
            r'Draw\.particles\(w,\s*h,\s*20,\s*0x[0-9A-Fa-f]+,\s*[0-9.]+f\);',
            r'',
            content
        )
        # تغییر خط اول به Plexus
        content = re.sub(
            r'Draw\.particles\(w,\s*h,\s*60,\s*0x[0-9A-Fa-f]+,\s*[0-9.]+f\);',
            r'Draw.plexusBackground(w, h, 0.45f);',
            content
        )
        
        with open(loadingart_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Patched LoadingArt.java")
    else:
        print("❌ LoadingArt.java not found!")

    print("🚀 All set! Gradle build should pass perfectly now.")

if __name__ == "__main__":
    fix_particle_errors()