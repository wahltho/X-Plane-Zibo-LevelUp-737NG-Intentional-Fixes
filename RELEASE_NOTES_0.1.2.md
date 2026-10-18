# Intentional Fixes 0.1.2

This release repairs ALT INTV handling in I30 and adds three fixes:

- I37: passed waypoint speed restrictions no longer return as cruise targets.
- I38: both FMCs reject CRZ speed edits while the displayed target belongs to
  MCP Speed Intervention. Existing pending speed edits are preserved.
- I39: W/STEP arrival fuel subtracts the extra step burn and converts the full
  result to the selected fuel unit.

No new pages, settings or features are added. The original `zibomod.xpl` stays
unchanged, and neither download contains a complete aircraft Lua file.

## Which download?

`X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-v0.1.2.zip` is the standalone
installer. It includes 17 fixes and accepts only the untouched original Zibo
4.05.35 FMS Lua, also used by LevelUp. It rejects a Lua file changed by other
patches. See [installation instructions](https://github.com/wahltho/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes/blob/v0.1.2/INSTALLATION.md).

`X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes-MTK-v0.1.2.zip` is the schema-5
source package for MTK catalog integration. It adds the CPDLC and LevelUp W&B
corrections only when those modules are selected. Earlier functional patches
come before Intentional Fixes; Lua Timer comes afterwards. The package format
requires MTK 0.21.1 or newer, but installation also requires a catalog that
qualifies and offers 0.1.2. Publishing this ZIP does not update the MTK catalog.
Do not copy its payloads manually into an aircraft.

Both ZIPs have a matching `.sha256` file.

## Updating

For standalone, first uninstall the old version with the installer and backups
that created it. Do not use the new installer to remove an older version or
delete its backups and ownership receipts. Then install 0.1.2 on the restored
original .35 file. There is no in-place upgrade. This release also includes the
standalone ownership and rollback guards added since the first release.

Keep MTK installations under MTK management and wait for the catalog update.
To switch installation methods, uninstall through the current owner first.
Close X-Plane and keep an aircraft backup before making changes.

## Checks and limits

The fix payloads passed 11 package, installer and focused behavior tests,
including I30 and I37-I39. All 576 FMS source-composition cases passed against
released MTK 0.29.4 and catalog 2.0.2. The six fully combined scripts loaded
under LuaJIT and passed 72 behavior method executions across Lua 5.4 and
LuaJIT. Release packaging preserves those exact payloads and the installer;
version metadata and documentation were updated afterwards.

These are dry tests, not simulator acceptance, a complete ALT INTV
certification, or a full-aircraft MTK installation/recovery test. MTK catalog
qualification remains separate. Details are in the
[test report](https://github.com/wahltho/X-Plane-Zibo-LevelUp-737NG-Intentional-Fixes/blob/v0.1.2/DRY_TEST_RESULTS_2026_10_18.txt).

This is an unofficial patch, not affiliated with, endorsed by, or supported by
Zibo, LevelUp or Laminar Research. Support and discussion belong on the
[wahltho Discord server](https://discord.gg/ySS88PMuyC), not the official
aircraft support channels. Provided as-is; keep your backups.
