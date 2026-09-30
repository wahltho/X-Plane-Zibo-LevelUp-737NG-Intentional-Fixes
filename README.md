# Zibo / LevelUp 737NG Intentional Fixes

This optional patch fixes several FMS issues in the original Zibo 4.05.35 Lua,
also used by LevelUp. It covers procedure courses, holds, approach reference
data, N1 mode changes, go-around detection and VNAV descent behavior. The full
list is in the [fix catalog](FIX_CATALOG.md).

**This is an unofficial patch.** It is not affiliated with, endorsed by, or
supported by Zibo, LevelUp or Laminar Research. For help, use the
[wahltho Discord server](https://discord.gg/ySS88PMuyC), not the official
aircraft support channels.

## Installation

Use the **X-Plane 737NG Maintenance Toolkit** to install Intentional Fixes
alongside other patches. Select it in the Zibo or LevelUp patch group. Toolkit
0.21.1 or newer is required. The Toolkit applies the functional patches first,
then Intentional Fixes. The CPDLC and LevelUp W&B fixes are applied only when
those modules are selected.

The **standalone installer** is for an untouched original .35 Lua file only.
It includes 14 fixes and rejects files changed by other Lua patches. See the
[installation instructions](INSTALLATION.md). If you have already used the
standalone installer, uninstall it before switching to Toolkit management.

The standalone download is version 0.1.0. The separate 0.1.1 MTK package is
for Toolkit installation; it does not replace the standalone installer.

## What changes

The patch updates `B738.a_fms.lua` in your aircraft installation. It adds no
FMC pages, settings or automatic services. `zibomod.xpl` stays unchanged, and
the download contains no complete aircraft Lua file.

The catalog lists 18 items. Fourteen are included in both installation paths;
two require CPDLC or LevelUp W&B. The remaining two are already handled by
CPDLC 1.2 or the original .35 Lua and need no further change.

## Testing and support

Automated checks cover patch application, repeated installation, restoration
and Lua syntax. The 18-case combination check and standalone installer tests
passed. These results do not establish how every fix behaves in the simulator;
see [test results](DRY_TEST_RESULTS.md) for what was checked.

Close X-Plane before installing and keep your own aircraft backup. If you run
into a problem, report it on the [wahltho Discord server](https://discord.gg/ySS88PMuyC).
The package is provided as-is; see [LICENSE](LICENSE).

For technical details, see [SOURCE.md](SOURCE.md),
[PATCH_MATRIX.md](PATCH_MATRIX.md) and `package-plan.json`.
