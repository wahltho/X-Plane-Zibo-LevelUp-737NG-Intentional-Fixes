# Intentional Fixes v0.1.0

This is the first public release of an independent, unofficial fix-only Lua
package for the original Zibo 4.05.35 FMS Lua currently shared by Zibo and
LevelUp.

The clean standalone installer contains 14 unconditional fix families. The
full source package also contains the conditional CPDLC and LevelUp W&B
corrections used by Maintenance Toolkit composition. See `FIX_CATALOG.md` for
the complete behavior list.

The release never distributes a complete aircraft Lua file and never changes
`zibomod.xpl`. The standalone installer rejects anything except the exact clean
.35 source; use the Maintenance Toolkit when other Lua patches are installed.

Dry validation is green. Simulator-runtime validation remains separate and is
not claimed by this release.

This project is not affiliated with, endorsed by, or supported by Zibo,
LevelUp or Laminar Research. Support is provided only through the
[wahltho Discord server](https://discord.gg/ySS88PMuyC). Do not request support
for this package through official Zibo, LevelUp or Laminar Research channels.
