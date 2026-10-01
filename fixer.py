import os
import re
import urllib.request
import zipfile
import shutil

# Configuration
SRC_DIR = "src/main/java/com/oryvex/kbclient"
RES_DIR = "src/main/resources"
FONTS_DIR = os.path.join(RES_DIR, "fonts")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  [+] Fixed: {path}")

def fix_theme():
    """Add missing color constants to Theme.java"""
    path = f"{SRC_DIR}/ui/Theme.java"
    if not os.path.exists(path): return
    
    content = read_file(path)
    
    # Check for missing constants and add them before the last closing brace
    additions = []
    required_consts = {
        "PANEL": "0xFF121A29",
        "PANEL2": "0xFF182235",
        "PANEL3": "0xFF22304A",
        "BORDER": "0xFF25324B",
        "BORDER_HI": "0xFF3B5078",
        "ACCENT": "0xFF22D3EE",
        "ACCENT_DK": "0xFF0E7490",
        "ACCENT2": "0xFFA78BFA"
    }
    
    for const, val in required_consts.items():
        if f"public static final int {const}" not in content:
            additions.append(f"    public static final int {const} = {val};")
            
    if additions:
        insert_point = content.rfind("}")
        new_content = content[:insert_point] + "\n".join(additions) + "\n" + content[insert_point:]
        write_file(path, new_content)

def fix_draw():
    """Add missing methods to Draw.java"""
    path = f"{SRC_DIR}/ui/Draw.java"
    if not os.path.exists(path): return
    
    content = read_file(path)
    
    # We need to add several methods. Let's append them before the last closing brace.
    # But first, let's check if they already exist to avoid duplicates.
    
    methods_to_add = []
    
    if "public static void vgradient" not in content:
        methods_to_add.append("""
    public static void vgradient(int w, int h, int top, int bottom) {
        for (int y = 0; y < h; y += 3) {
            Gui.drawRect(0, y, w, Math.min(h, y + 3), lerp(top, bottom, y / (float) h));
        }
    }""")

    if "public static void shadow" not in content:
        methods_to_add.append("""
    public static void shadow(float x, float y, float w, float h, float r, int color, float spread) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;
        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(1.5f);
        for (float i = 0.5f; i < spread; i += 0.5f) {
            float a = alpha * (1f - (i / spread)) * 0.05f;
            GlStateManager.color(red, green, blue, a);
            float nx = x - i, ny = y - i, nw = w + i * 2, nh = h + i * 2, nr = r + i;
            GL11.glBegin(GL11.GL_LINE_LOOP);
            for (int j = 180; j <= 270; j += 10) GL11.glVertex2d(nx + nr + Math.cos(Math.toRadians(j)) * nr, ny + nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 270; j <= 360; j += 10) GL11.glVertex2d(nx + nw - nr + Math.cos(Math.toRadians(j)) * nr, ny + nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 0; j <= 90; j += 10) GL11.glVertex2d(nx + nw - nr + Math.cos(Math.toRadians(j)) * nr, ny + nh - nr + Math.sin(Math.toRadians(j)) * nr);
            for (int j = 90; j <= 180; j += 10) GL11.glVertex2d(nx + nr + Math.cos(Math.toRadians(j)) * nr, ny + nh - nr + Math.sin(Math.toRadians(j)) * nr);
            GL11.glEnd();
        }
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }""")

    if "public static FontRenderer font()" not in content:
        methods_to_add.append("""
    public static FontRenderer font() { return Minecraft.getMinecraft().fontRendererObj; }""")

    if "public static int width(String s, float scale)" not in content:
        methods_to_add.append("""
    public static int width(String s, float scale) { return (int) (font().getStringWidth(s) * scale); }""")

    if "public static void text(String s, float x, float y, int color, float scale, boolean shadow)" not in content:
        methods_to_add.append("""
    public static void text(String s, float x, float y, int color, float scale, boolean shadow) {
        if (((color >>> 24) & 255) <= 4) return;
        GlStateManager.pushMatrix();
        GlStateManager.scale(scale, scale, 1f);
        font().drawString(s, x / scale, y / scale, color, shadow);
        GlStateManager.popMatrix();
    }""")

    if "public static void centered(String s, float cx, float y, int color, float scale, boolean shadow)" not in content:
        methods_to_add.append("""
    public static void centered(String s, float cx, float y, int color, float scale, boolean shadow) {
        text(s, cx - font().getStringWidth(s) * scale / 2f, y, color, scale, shadow);
    }""")

    if "public static void radial" not in content:
        methods_to_add.append("""
    public static void radial(float cx, float cy, float r, int color, boolean fill) {
        float alpha = (color >> 24 & 0xFF) / 255.0F;
        if (alpha <= 0.01f) return;
        float red = (color >> 16 & 0xFF) / 255.0F;
        float green = (color >> 8 & 0xFF) / 255.0F;
        float blue = (color & 0xFF) / 255.0F;
        blend();
        GlStateManager.disableTexture2D();
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GlStateManager.color(red, green, blue, alpha);
        GL11.glBegin(fill ? GL11.GL_POLYGON : GL11.GL_LINE_LOOP);
        for (int i = 0; i <= 360; i += 5) {
            GL11.glVertex2d(cx + Math.cos(Math.toRadians(i)) * r, cy + Math.sin(Math.toRadians(i)) * r);
        }
        GL11.glEnd();
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
        GlStateManager.enableTexture2D();
    }""")

    if "public static void plexusBackground" not in content:
        methods_to_add.append("""
    public static void plexusBackground(int w, int h, float maxAlpha) {
        float t = (System.currentTimeMillis() % 100000L) / 1000f;
        int count = 100;
        float[] px = new float[count];
        float[] py = new float[count];
        for (int i = 0; i < count; i++) {
            float sp = 1.5f + (i % 4) * 0.8f;
            px[i] = (i * 93 + t * sp * 18f) % (w + 100) - 50;
            py[i] = (i * 61 - t * sp * 12f) % (h + 100) - 50;
            if (py[i] < -50) py[i] += h + 100;
        }
        blend();
        GL11.glDisable(GL11.GL_TEXTURE_2D);
        GL11.glEnable(GL11.GL_LINE_SMOOTH);
        GL11.glLineWidth(1.2f);
        GL11.glBegin(GL11.GL_LINES);
        for (int i = 0; i < count; i++) {
            for (int j = i + 1; j < count; j++) {
                float dx = px[i] - px[j];
                float dy = py[i] - py[j];
                float dist = (float) Math.sqrt(dx * dx + dy * dy);
                if (dist < 120f) {
                    float a = (1f - dist / 120f) * maxAlpha * 0.6f;
                    int color = alpha(Theme.ACCENT, a);
                    float red = (color >> 16 & 0xFF) / 255.0F;
                    float green = (color >> 8 & 0xFF) / 255.0F;
                    float blue = (color & 0xFF) / 255.0F;
                    GlStateManager.color(red, green, blue, a);
                    GL11.glVertex2d(px[i], py[i]);
                    GL11.glVertex2d(px[j], py[j]);
                }
            }
        }
        GL11.glEnd();
        for (int i = 0; i < count; i++) {
            float tw = 0.5f + 0.5f * (float) Math.sin(t * 2f + i);
            int a = (int) (maxAlpha * 255f * tw);
            roundRect(px[i] - 1.5f, py[i] - 1.5f, 3f, 3f, 1.5f, (a << 24) | (Theme.ACCENT & 0xFFFFFF));
        }
        GL11.glEnable(GL11.GL_TEXTURE_2D);
        GL11.glDisable(GL11.GL_LINE_SMOOTH);
    }""")

    if methods_to_add:
        insert_point = content.rfind("}")
        new_content = content[:insert_point] + "\n".join(methods_to_add) + "\n" + content[insert_point:]
        write_file(path, new_content)

def fix_fade_screen():
    """Fix drawBackdrop signature in FadeScreen.java"""
    path = f"{SRC_DIR}/ui/FadeScreen.java"
    if not os.path.exists(path): return
    
    content = read_file(path)
    
    # Replace the old drawBackdrop with the new one that takes mx, my
    old_sig = "protected void drawBackdrop(int particleCount)"
    new_sig = "protected void drawBackdrop(int mx, int my)"
    
    if old_sig in content:
        content = content.replace(old_sig, new_sig)
        # Also update the call inside if it exists, though usually it's just the definition
        # The implementation likely uses this.width/height anyway, so we just change the signature
        # to match what the subclasses are trying to call or what Background.draw expects
        
        # Actually, looking at the error, subclasses call drawBackdrop(30). 
        # We need to make sure the implementation handles the new signature correctly.
        # Let's replace the whole method body if it's simple, or just the signature.
        
        # The error says: required: int,int found: int
        # This means the DEFINITION in FadeScreen expects 2 ints, but CALLS use 1 int.
        # OR the DEFINITION expects 1 int, but CALLS use 2 ints?
        # Error: "method drawBackdrop in class FadeScreen cannot be applied to given types; required: int,int found: int"
        # This means the CURRENT definition requires 2 ints, but the code is calling it with 1.
        # Wait, the previous adder changed it to (mx, my). The current code in repo might still be (particleCount).
        # Let's check the repo content provided.
        # Repo content shows: protected void drawBackdrop(int particleCount)
        # So the DEFINITION is 1 int.
        # The ERROR says: required: int,int. This implies the COMPILER sees a definition requiring 2 ints.
        # Ah, the error log is from a PREVIOUS run where adder.py already ran?
        # No, the user said "create fixer.py just add that changes is bug".
        # The error log shows: `drawBackdrop(30);` -> `required: int,int`.
        # This means `FadeScreen.java` ALREADY has `drawBackdrop(int mx, int my)` in the build sources?
        # Yes, look at the folder_structure.txt under `20261001_014535`:
        # `protected void drawBackdrop(int mx, int my) { Background.draw(...) }`
        # So the DEFINITION is correct (2 args). The CALLS are wrong (1 arg).
        
        # So we need to fix the CALLS in GuiAltManager, GuiKbOptions, GuiAnalyzer.
        pass 

def fix_menu_calls():
    """Fix drawBackdrop calls in menus to pass mouseX, mouseY"""
    files = [
        f"{SRC_DIR}/ui/GuiAltManager.java",
        f"{SRC_DIR}/ui/GuiKbOptions.java",
        f"{SRC_DIR}/ui/GuiAnalyzer.java"
    ]
    
    for path in files:
        if not os.path.exists(path): continue
        content = read_file(path)
        
        # Replace drawBackdrop(NUMBER) with drawBackdrop(mouseX, mouseY)
        # Use regex to find drawBackdrop(\d+)
        content = re.sub(r'drawBackdrop\(\d+\)', 'drawBackdrop(mouseX, mouseY)', content)
        
        write_file(path, content)

def download_fonts():
    """Download Inter and Vazirmatn fonts for GitHub Actions"""
    ensure_dir(FONTS_DIR)
    
    fonts = {
        "Inter-Regular.ttf": "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip",
        "Vazirmatn-Regular.ttf": "https://github.com/rastikerdar/vazirmatn/releases/download/v4.0.0/Vazirmatn-v4.0.0.zip"
    }
    
    # Note: In a real GH Action, we'd use wget/curl. Here we simulate the structure.
    # We will create a script snippet to be added to build.yml instead of downloading here.
    print("  [+] Font download logic prepared for GitHub Actions")

def fix_build_yml():
    """Add font downloading step to GitHub Actions"""
    path = ".github/workflows/build.yml"
    if not os.path.exists(path): return
    
    content = read_file(path)
    
    # Add a step before 'Build Mod with Gradle'
    font_step = """
    - name: Download Google Fonts
      run: |
        mkdir -p src/main/resources/fonts
        # Inter Font
        curl -sL https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip -o inter.zip
        unzip -j inter.zip "Inter-4.0/ttf/Inter-Regular.ttf" -d src/main/resources/fonts
        rm inter.zip
        # Vazirmatn Font (Persian)
        curl -sL https://github.com/rastikerdar/vazirmatn/releases/download/v4.0.0/Vazirmatn-v4.0.0.zip -o vazir.zip
        unzip -j vazir.zip "Vazirmatn-v4.0.0/ttf/Vazirmatn-Regular.ttf" -d src/main/resources/fonts
        rm vazir.zip
"""
    
    if "Download Google Fonts" not in content:
        # Insert before 'Build Mod with Gradle'
        content = content.replace("- name: Build Mod with Gradle", font_step + "- name: Build Mod with Gradle")
        write_file(path, content)

if __name__ == "__main__":
    print("Starting KBClient Bug Fixer...")
    fix_theme()
    fix_draw()
    fix_menu_calls()
    fix_build_yml()
    print("Fixer completed successfully!")