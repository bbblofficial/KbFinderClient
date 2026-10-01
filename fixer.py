#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adder.py - 1.8.9 fix: ScoreObjective.getDisplayName() returns String,
not IChatComponent. Drop the .getFormattedText() calls.

Run from the project root:
    python adder.py
"""

import os, sys, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(ROOT, "src", "main", "java",
                    "com", "oryvex", "kbclient", "TransparentOverlays.java")

STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    if not os.path.isfile(FILE):
        print("!! not found:", FILE)
        print("   Run this from the project root (where build.gradle is).")
        sys.exit(1)

    with open(FILE, "r", encoding="utf-8") as f:
        src = f.read()
    orig = src

    # 1) line 77: width calc
    src = src.replace(
        "objective.getDisplayName().getFormattedText());",
        "objective.getDisplayName());"
    )

    # 2) line 108: title assignment
    src = src.replace(
        "String title = objective.getDisplayName().getFormattedText();",
        "String title = objective.getDisplayName();"
    )

    if src == orig:
        print("Nothing to change - the file is already fixed (or pattern differs).")
        print("Current occurrences of '.getFormattedText()':",
              src.count(".getFormattedText()"))
        return

    shutil.copy2(FILE, FILE + ".bak_" + STAMP)
    with open(FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)

    print("patched", os.path.relpath(FILE, ROOT))
    print("remaining '.getFormattedText()' occurrences:",
          src.count(".getFormattedText()"))
    print()
    print(">>> now commit and push <<<")
    print("    git add -A")
    print('    git commit -m "1.8.9: ScoreObjective.getDisplayName() returns String"')
    print("    git push")


if __name__ == "__main__":
    main()