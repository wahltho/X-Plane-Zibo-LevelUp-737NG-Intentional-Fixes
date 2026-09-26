# Zibo / LevelUp 737NG Intentional Fixes

> **Independent, unofficial community patch.** This project is not affiliated
> with, endorsed by, or supported by Zibo, LevelUp or Laminar Research.
> Support is provided only through the
> [wahltho Discord server](https://discord.gg/ySS88PMuyC). Please do not request
> support for this package through official Zibo, LevelUp or Laminar Research
> support channels.

Optional, fix-only Lua corrections for the original Zibo/LevelUp Lua FMS. Both
aircraft currently use the same original Zibo 4.05.35 `B738.a_fms.lua`; that
single Lua hash is the clean baseline. The package leaves the upstream
`zibomod.xpl` unchanged and never distributes the complete aircraft Lua file.

The source closure contains 18 fix families. Sixteen families carry a Lua
delta in 15 structural payload documents because I02 and I03 share one owner;
I14 is already satisfied by a selected CPDLC 1.2 surface and I29 is already
satisfied by the shared clean baseline. `package-plan.json` is the authoritative
source order and condition map.

The user-facing inventory and detailed behavior descriptions are in
`FIX_CATALOG.md`; `PATCH_MATRIX.md` remains the compact engineering-status view.

The package-local 18-case composition and Lua-syntax dry matrix is green; see
`DRY_TEST_RESULTS.md`. Simulator behavior remains a separate validation gate
and is not claimed by the dry evidence.

A strict standalone installer source is available as `z_Install.py`; see
`INSTALLATION.md`. It accepts only the untouched shared original .35 Lua and
installs the 13 unconditional payload documents representing 14 fix families.
Aircraft with any other Lua patch must use the Maintenance Toolkit.

Product rules:

- one user-visible `Intentional Fixes` selection, installed after all selected
  functional modules;
- fixes only: no new user-visible functions, pages, options, settings or
  automatic services; private helpers are allowed only when a bounded fix
  requires them;
- never distribute or replace the complete upstream `B738.a_fms.lua`;
- conditional CPDLC and LevelUp W&B hardening only when those modules are
  already selected;
- unknown or structurally incompatible input blocks the transaction.

The authored payload anchors are unique on the shared .35 clean baseline and
do not overlap within a payload. The conditional I06 anchors do not overlap the
CPDLC 1.2 exact-replacement owners; I33 deliberately targets the completed
LevelUp W&B surface. The complete composed Lua passes dry syntax and idempotence
checks, but simulator behavior remains a separate gate.

## Support and disclaimer

For installation or package support, use only the
[wahltho Discord server](https://discord.gg/ySS88PMuyC). This is not an
official Zibo, LevelUp or Laminar Research product, and their support channels
do not cover it. Keep an aircraft backup, close X-Plane before installation,
and use the package at your own risk. The software is provided as-is without
warranty; see `LICENSE`.
