# KB Client 3.0 (Minecraft 1.8.9 Forge)

Modern-UI client + knockback profile detector for Carbon / Spigot servers.

## What's new in 3.0
* Every screen fades in; every KB Client screen also fades out.
  Vanilla screens (pause menu, inventory, world select...) fade in, and closing
  back to the game plays a soft world fade.
* Fully custom loading screen: world loading, world saving and terrain download.
* Custom Options button (animated gear) on the main menu and the pause menu,
  plus a custom Options screen (HUD, particles, toasts, loading screen, fade speed).
* New detector + exact YAML parser (see below).

## The 12 parameters
ONE-POINT-SEVEN, HORIZONTAL, VERTICAL, EXTRA-HORIZONTAL, EXTRA-VERTICAL, FRICTION,
Y-LIMIT, DAMAGE-TICKS.OVERRIDE, DAMAGE-TICKS.VALUE, DYNAMIC-LIMIT, LIMIT-HORIZONTAL, H-LIMIT

### Exact extraction (YAML parser)
`/kb import` (clipboard) or `/kb import file.yml` (from .minecraft/kbclient/) or the
Import button parses a Carbon config exactly as written: comments ignored (full-line
and inline), nested sections (DAMAGE-TICKS -> OVERRIDE / VALUE), booleans, decimals
and integers. All 12 keys are read, none defaulted. Missing / unparsable keys are
listed explicitly. `/kb sample` loads a built-in example.
The Compare tab shows Detected vs Reference with deltas.

### Packet detector
Every velocity packet (S12) is snapshotted and fitted with the Carbon model
    new = old / FRICTION + dir * (HORIZONTAL [+ EXTRA-HORIZONTAL if attacker sprints])
    newY = oldY / FRICTION + VERTICAL [+ EXTRA-VERTICAL], clamped to Y-LIMIT
Each value shows a source tag: MEAS (measured), EST (estimated / lower bound),
DEF (not observable yet), FILE (imported).

Some keys are NOT physically observable from packets alone:
  * DAMAGE-TICKS.VALUE while OVERRIDE is false (vanilla 20 is in effect)
  * H-LIMIT while LIMIT-HORIZONTAL is false (never clamps)
Use the YAML import for the exact values of those.

To raise confidence: get hit by a walking AND a sprinting player, while standing
and while moving, on the ground AND while falling, and let someone click fast.

## Controls
  * Right Shift - open analyzer      * /kb - open analyzer
  * /kb start 15 | stop | resume | reset | export | hud | status | yaml
  * /kb import [file] | sample | clear
  * Exports go to .minecraft/kbclient/*.yml and *-samples.csv
