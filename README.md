# Zibo / LevelUp 737NG Intentional Fixes

This optional patch fixes several FMS issues in the original Zibo 4.05.35 Lua,
also used by LevelUp. It covers procedure courses, holds, approach reference
data, N1 mode changes, go-around detection and VNAV descent behavior. The full
list is in the [fix catalog](FIX_CATALOG.md).

Version 0.1.2 repairs I30 ALT INTV handling and adds I37-I39 cruise speed and
W/STEP fuel corrections. Both packages use the same fix payloads. See the
[release notes](RELEASE_NOTES_0.1.2.md) and
[test results](DRY_TEST_RESULTS_2026_10_18.txt).

**This is an unofficial patch.** It is not affiliated with, endorsed by, or
supported by Zibo, LevelUp or Laminar Research. For help, use the
[wahltho Discord server](https://discord.gg/ySS88PMuyC), not the official
aircraft support channels.

## Installation

Use the **X-Plane 737NG Maintenance Toolkit** to install Intentional Fixes
alongside other patches. Select it in the Zibo or LevelUp patch group. Toolkit
0.21.1 or newer is required by the package format. Version 0.1.2 must also be
qualified and offered by the Toolkit catalog before it can be installed there;
publishing the MTK ZIP alone does not update the catalog. The Toolkit applies earlier functional patches
before Intentional Fixes; Lua Timer follows afterwards. The CPDLC and LevelUp
W&B fixes are applied only when those modules are selected.

The **standalone installer** is for an untouched original .35 Lua file only.
Version 0.1.2 includes 17 fixes.
It rejects files changed by other Lua patches. See the
[installation instructions](INSTALLATION.md). If you have already used the
standalone installer, uninstall it before switching to Toolkit management.

Both downloads are version 0.1.2:

- [Standalone installer](https://github.com/wahltho/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes/releases/download/v0.1.2/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-v0.1.2.zip)
- [MTK source package](https://github.com/wahltho/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes/releases/download/v0.1.2/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-MTK-v0.1.2.zip) for catalog integration, not standalone installation.

To update an older standalone installation, uninstall it with its original
installer first. Keep its backups until removal succeeds. Then install 0.1.2
on the restored original .35 file; there is no in-place upgrade.

## What changes

The patch updates `B738.a_fms.lua` in your aircraft installation. It adds no
FMC pages, settings or automatic services. `zibomod.xpl` stays unchanged, and
the download contains no complete aircraft Lua file.

The current source catalog lists 21 items. Seventeen apply to both installation paths;
two require CPDLC or LevelUp W&B. The remaining two are already handled by
CPDLC 1.2 or the original .35 Lua and need no further change.

## Testing and support

The fix payloads pass 11 package, installer and focused behavior tests,
including I30 and I37-I39. All 576 FMS combinations pass with released MTK
0.29.4 and catalog 2.0.2. The six fully combined outputs also pass the behavior
tests under Lua 5.4 and LuaJIT. Full-aircraft MTK installation/recovery, release
qualification and simulator acceptance remain separate checks; see
[test results](DRY_TEST_RESULTS.md).

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
