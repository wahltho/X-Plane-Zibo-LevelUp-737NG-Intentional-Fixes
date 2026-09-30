# Standalone installation

Use this installer only with an untouched original Zibo 4.05.35 Lua file.
The same Lua file is used by LevelUp.

If you already have CPDLC, LevelUp W&B, VNAV or another Lua patch installed,
use the **X-Plane 737NG Maintenance Toolkit** instead. Select Intentional
Fixes in the Zibo or LevelUp patch group. Toolkit 0.21.1 or newer is required.

This installer is unofficial and is not supported by Zibo, LevelUp or
Laminar Research. For help, use the
[wahltho Discord server](https://discord.gg/ySS88PMuyC), not the official
aircraft support channels.

## Install

Close X-Plane and keep your own aircraft backup. Open a terminal in this
package's directory. Replace the example path below with your aircraft folder
(for Zibo or LevelUp), not the X-Plane folder.

First, check that the aircraft can be patched. This does not change any files:

```text
python3 z_Install.py check --aircraft-root "/path/to/B737-800X"
```

If the check succeeds, install:

```text
python3 z_Install.py install --aircraft-root "/path/to/B737-800X"
```

The installer saves the original Lua in `.zibo-intentional-fixes-clean35/`
inside the aircraft folder before applying the fixes. Keep this folder: it is
needed to uninstall. Running install again checks the installed file without
applying the fixes a second time.

To check an existing installation:

```text
python3 z_Install.py verify --aircraft-root "/path/to/B737-800X"
```

## Uninstall or switch to the Toolkit

Use the same installer to restore the saved original:

```text
python3 z_Install.py uninstall --aircraft-root "/path/to/B737-800X"
```

If the Lua has been changed since installation, uninstall refuses to overwrite
it. Do not remove the backup folder or try to force the operation; ask for help
on the wahltho Discord server.

Uninstall before switching to Toolkit management. The Toolkit does not adopt
the standalone installer's backup.

## Included fixes

The standalone installer includes 14 fixes: I01–I05, I07–I09, I16, I24,
I27, I30, I34 and I35. See the [fix catalog](FIX_CATALOG.md) for descriptions.

It does not include the CPDLC or LevelUp W&B fixes. I29 needs no patch because
the original .35 Lua already handles it.

## Accepted original file

The installer checks the contents of `B738.a_fms.lua`, not just the aircraft's
version label. It accepts only this SHA-256:

```text
ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e
```

A different version or a file edited by another patch is rejected.
