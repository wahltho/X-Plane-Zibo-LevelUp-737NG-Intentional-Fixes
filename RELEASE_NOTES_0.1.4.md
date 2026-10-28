# Intentional Fixes 0.1.4

This fixes a startup-order error introduced in 0.1.3. The patch registered an
LNAV command wrapper while the FMS script was loading. If the native command
was not available yet, XLua could stop loading the script, leaving the FMS
unavailable and potentially affecting other cockpit functions.

Registration now waits for the command and retries from the lifecycle callbacks.
It runs once when the command is available. A missing command no longer aborts
FMS loading. This does not add settings or change which fixes are selected.

## Update

Close X-Plane. In MTK, check the patches for the selected aircraft, review the
selection and apply Intentional Fixes 0.1.4. Keep your other selected patches.
MTK 0.31.0 or newer follows compatible patch releases automatically; update MTK
through its built-in updater first if needed. Restart X-Plane afterwards.

For standalone installations, uninstall with the original installer and retain
its backups, then install 0.1.4 on the restored original .35 Lua file. Do not
mix standalone and MTK ownership. See [installation instructions](INSTALLATION.md).

## Verification

51 focused composition cases pass using released MTK 0.31.1 patch handlers.
56 offline startup cases pass for standalone and fully combined Zibo/LevelUp
FMS scripts, including immediate, delayed and permanently unavailable commands.
The old-code negative control reproduces the loading failure. Existing
regression tests pass. See [the report](STARTUP_REGRESSION_2026_10_28.md).

These checks are not a simulator or flight test, and do not establish that every
reported radio/FMS problem has this cause. No complete aircraft Lua is included.
This is an independent, unofficial patch; support is on my Discord:
https://discord.gg/ySS88PMuyC
