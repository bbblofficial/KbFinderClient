import os

def fix_alt_manager():
    filepath = "src/main/java/com/oryvex/kbclient/ui/GuiAltManager.java"
    
    if not os.path.exists(filepath):
        print(f"❌ Error: Could not find {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # جایگزینی متد keyTyped با onKey که متد استاندارد FadeScreen است
    if "protected void keyTyped(char typedChar, int keyCode)" in content:
        content = content.replace(
            "protected void keyTyped(char typedChar, int keyCode)",
            "protected void onKey(char typedChar, int keyCode)"
        )
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        print("✅ Fixed GuiAltManager.java! (Changed keyTyped to onKey)")
    else:
        print("ℹ️ No changes needed or keyTyped not found.")

if __name__ == "__main__":
    fix_alt_manager()