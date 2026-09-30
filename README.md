# KB Client 2.0 (Minecraft 1.8.9 Forge)

Modern-UI client + live knockback profile detector for Carbon / Spigot servers.

## How the detector works
Every time the server sends you a velocity packet (S12) the mod snapshots:
  * the knockback vector (H / V)
  * your own motion right before the hit
  * the attacker (nearest player, aligned with the knockback direction):
    sprinting?, knockback enchant?, distance, direction
  * the tick time between hits

It then solves the Carbon model
    new = old / FRICTION + dir * (HORIZONTAL + EXTRA-HORIZONTAL if sprint)
    newY = oldY / FRICTION + VERTICAL (+ EXTRA-VERTICAL if sprint), capped by Y-LIMIT
with a grid-search least-squares fit, plus clamp/plateau detection for
Y-LIMIT / H-LIMIT, and hit-gap analysis for DAMAGE-TICKS.

Every value has a confidence bar. Low bars mean "hit me more / differently":
  * get hit by a NON-sprinting AND a SPRINTING player  -> HORIZONTAL / EXTRA-*
  * get hit while standing still AND while moving       -> FRICTION
  * get hit in mid-air at different heights             -> Y-LIMIT / DYNAMIC-LIMIT
  * get hit rapidly (fast clicking)                     -> DAMAGE-TICKS

## Controls
  * Right Shift  - open analyzer in-game
  * /kb          - open analyzer
  * /kb start 15 - record exactly 15 hits then stop
  * /kb stop | resume | reset | export | hud | status | yaml
  * Exports go to  .minecraft/kbclient/*.yml and *-samples.csv
