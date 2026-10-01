import os
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(BASE, ".fixer_backup", "20260930_222156", "src", "main", "java", "com", "oryvex", "kbclient")
TARGET = os.path.join(BASE, "src", "main", "java", "com", "oryvex", "kbclient")

FILES = [
    "KBTracker.java",
    os.path.join("kb", "KBEstimator.java"),
    os.path.join("kb", "KBProfile.java"),
    os.path.join("kb", "KBSample.java"),
]

def main():
    print("🔄 Restoring KB files to original version...\n")
    ok = 0
    for f in FILES:
        src = os.path.join(BACKUP, f)
        dst = os.path.join(TARGET, f)
        if not os.path.exists(src):
            print(f"  ⚠️  Not found in backup: {f}")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✅ Restored: {f}")
        ok += 1
    print(f"\n✨ Done — {ok}/{len(FILES)} files restored to default.")

if __name__ == "__main__":
    main()