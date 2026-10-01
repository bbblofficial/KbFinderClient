import os
import re

def main():
    font_file = os.path.join("src", "main", "java", "com", "oryvex", "kbclient", "font", "ModernFontRenderer.java")
    
    if not os.path.exists(font_file):
        print(f"File not found: {font_file}")
        return

    with open(font_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix 1: Remove the invalid @Override bidiReorder method completely
    # (Regex matches the method and everything inside its brackets)
    content = re.sub(r'\s*@Override\s*public String bidiReorder\(String text\) \{[^}]*\}', '', content)

    # Fix 2: Provide a custom color array since the parent's `colorCode` is private
    custom_colors = """
    private static final int[] CUSTOM_COLOR_CODES = new int[32];
    static {
        for (int i = 0; i < 32; ++i) {
            int j = (i >> 3 & 1) * 85;
            int k = (i >> 2 & 1) * 170 + j;
            int l = (i >> 1 & 1) * 170 + j;
            int i1 = (i >> 0 & 1) * 170 + j;
            if (i == 6) k += 85;
            if (i >= 16) { k /= 4; l /= 4; i1 /= 4; }
            CUSTOM_COLOR_CODES[i] = (k & 255) << 16 | (l & 255) << 8 | i1 & 255;
        }
    }

    private int renderText"""

    if "CUSTOM_COLOR_CODES" not in content:
        # Inject the custom color array right above the renderText method
        content = content.replace("    private int renderText", custom_colors)
    
    # Replace the private variable reference with our new array
    content = content.replace("this.colorCode[colorIndex]", "CUSTOM_COLOR_CODES[colorIndex]")

    with open(font_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("Fix applied successfully!")
    print(" - Removed invalid bidiReorder override.")
    print(" - Replaced private colorCode access with CUSTOM_COLOR_CODES.")

if __name__ == "__main__":
    main()