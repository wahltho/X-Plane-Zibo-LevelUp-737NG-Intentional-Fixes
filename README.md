# Zibo / LevelUp 737NG Intentional Fixes

This optional patch fixes several FMS issues in the original Zibo 4.05.35 Lua,
also used by LevelUp. It covers procedure courses, holds, approach reference
data, N1 mode changes, go-around detection and VNAV descent behavior. The full
list is in the [fix catalog](FIX_CATALOG.md).

Version **0.1.4** fixes a startup-order error introduced in 0.1.3. If the native
LNAV command was not ready when the FMS script loaded, the script could stop
loading. Registration now waits until the command is available. See the
[release notes](RELEASE_NOTES_0.1.4.md).

**This is an unofficial patch.** It is not affiliated with, endorsed by, or
supported by Zibo, LevelUp or Laminar Research. For help, use the
[wahltho Discord server](https://discord.gg/ySS88PMuyC), not the official
aircraft support channels.

## Installation

Use the **X-Plane 737NG Maintenance Toolkit** to install Intentional Fixes
alongside other patches. Select it in the Zibo or LevelUp patch group. Toolkit
0.31.0 or newer follows compatible patch releases without a separate catalog
update for each patch version. Update MTK through its built-in updater first
if needed, then check the selected aircraft's patches. Older Toolkit versions
can remain restricted to the versions explicitly approved in their catalog.
The Toolkit applies
earlier functional patches before Intentional Fixes; Lua Timer follows afterwards. The CPDLC and LevelUp
W&B fixes are applied only when those modules are selected.

The **standalone installer** is for an untouched original .35 Lua file only.
Version 0.1.4 includes 18 fix families.
It rejects files changed by other Lua patches. See the
[installation instructions](INSTALLATION.md). If you have already used the
standalone installer, uninstall it before switching to Toolkit management.

Downloads for version 0.1.4:

- [Standalone installer](https://github.com/wahltho/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes/releases/download/v0.1.4/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-v0.1.4.zip)
- [MTK source package](https://github.com/wahltho/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes/releases/download/v0.1.4/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-MTK-v0.1.4.zip) for catalog integration, not standalone installation.

To update an older standalone installation, uninstall it with its original
installer first. Keep its backups until removal succeeds. A new version must
be installed on the restored original .35 file; there is no in-place upgrade.
Follow the [update instructions](INSTALLATION.md#updating-an-older-standalone-installation).

## What changes

The patch updates `B738.a_fms.lua` in your aircraft installation. It adds no
FMC pages, settings or automatic services. `zibomod.xpl` stays unchanged, and
the download contains no complete aircraft Lua file.

The catalog lists 22 items. Eighteen apply to both installation paths;
two require CPDLC or LevelUp W&B. The remaining two are already handled by
CPDLC 1.2 or the original .35 Lua and need no further change.

## Testing and support

The startup fix passes 51 focused FMS composition cases and 56 offline startup
cases for Zibo and LevelUp, including a delayed or missing LNAV command and
combined FMS patches. The existing regression suite also passes. These are
source and lifecycle tests, not simulator or flight validation. See the
[startup regression report](STARTUP_REGRESSION_2026_10_28.md). Historical 0.1.3
results remain in [the implementation report](IMPLEMENTATION_0.1.3.md).

Close X-Plane before installing and keep your own aircraft backup. If you run
into a problem, report it on the [wahltho Discord server](https://discord.gg/ySS88PMuyC).
The package is provided as-is; see [LICENSE](LICENSE).

For technical details, see [SOURCE.md](SOURCE.md),
[PATCH_MATRIX.md](PATCH_MATRIX.md) and `package-plan.json`.

## Installation ownership

MTK and the standalone installer remain separate supported installation methods.
Use the same owner for updates and removal. To switch, uninstall through the
current owner first, then install through the other. Neither installer adopts
already patched files on the strength of matching hashes alone.

Keep the complete extracted package, including `standalone_guard.py` and
`standalone-ownership.json`. The standalone installer checks its recorded
original backups and stops if MTK owns this patch or a shared target file.
Unknown, duplicate or incomplete patch blocks and unowned companion files also
block the operation. Other correctly installed patches are preserved.

A failed operation restores the bytes it changed. If the process is interrupted,
keep the `.patch-ownership` receipt, transaction journal and lock, together with
any older patch backup/state directory. Do not delete them to retry. Ask for
support before changing those files.

Older standalone installs without a complete receipt are not automatically
migrated. Remove them using the installer and original backups that created
them. The ownership checks do not adopt those installations. The dry-test scope
and remaining runtime checks are recorded in
[test results](DRY_TEST_RESULTS_2026_10_18.txt).
