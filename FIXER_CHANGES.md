# Fixer changes

Generated 2026-09-30 22:21

- Added `GlSafe` (OpenGL state push/pop/reset).
- Added `GuiStateFixer`: opens GuiMainMenu if the screen is null with no world (fixes black screen after Singleplayer -> Back).
- Registered `GuiStateFixer` in the main mod class.
- Wrapped loading-screen render methods in GL push/pop with try/finally.
