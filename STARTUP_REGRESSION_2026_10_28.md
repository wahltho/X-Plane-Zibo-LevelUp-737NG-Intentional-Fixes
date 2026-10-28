# FMS startup after Intentional Fixes 0.1.3

The published I40 payload calls `wrap_command` while the FMS script is loading.
XLua 1 looks up the native LNAV command immediately. If Zibomod has not registered
it yet, XLua passes nil to `XLuaWrapCommand`, which rejects it. The FMS chunk then
stops before registering `flight_start` and `after_physics`.

The original .35 FMS loads without this early lookup. A local negative control
restoring the early call reproduces the failure. This is a confirmed startup-order
defect. It fits the reported EFB ERROR 0, but without the affected session's Log.txt
it is not proof that every radio/FMS report has this exact cause.

## Change

Registration now runs from `flight_start` and `after_physics`. It checks whether
the command exists before wrapping it. If absent, the next frame tries again.
Once installed, the private flag prevents more lookups or duplicate wrappers,
including across another `flight_start`. The phase-zero LNAV refresh is unchanged.
The lookup supports the XLua 1 and XPLM API names. Actual registration exceptions
are not suppressed and do not mark a failed attempt as successful.

Only the I40 payload changes. Its standalone and MTK manifest sizes/hashes and
the standalone result hash were refreshed. No package version was published.

## Tests

`tests/test_load_startup.py` runs the complete FMS chunk, `flight_start` and six
`after_physics` callbacks with the original XLua namespace implementation.
The native API is a test fixture: datarefs have bounded storage, command
availability is controlled, and timers do not execute. Airport-cache generation
is excluded; file reads return unavailable and file writes go to an in-memory
sink. No live aircraft or simulator is accessed.

Cases cover command availability at load, at flight start, after two frames,
and never; single registration; no lookups after success; another flight start;
and a negative control with the old early registration. Component tests check
phase-zero behavior and propagation of genuine registration errors. The alternate
XPLM lookup is an API-contract case, not an XLua 2 binary/runtime test.

Additional composed scripts can be supplied with `INTENTIONAL_STARTUP_FIXTURES`
(path separator list) and released helper modules with `INTENTIONAL_STARTUP_HELPERS`.
Set `LUAJIT` and optionally `XLUA_STARTUP_INIT` to select the local interpreter/glue.

The focused composition matrix uses the released MTK 0.31.1 patch handlers.
It covers Intentional Fixes alone, each FMS companion individually, and all
companions together, in original, LF and CRLF-with-BOM forms: 24 Zibo and
27 LevelUp cases, all passing. Companions are VNAV, AUTO JETWAY, CPDLC, VREF,
27K, Timer Mod and, for LevelUp, W&B. Each selection is composed twice from
the verified original and must be byte-identical. The all-selected outputs
also accept Intentional Fixes reapplication unchanged. This is source-composition
coverage, not a full-aircraft update/restore transaction test. Companion versions
and hashes are pinned in the evidence; this run uses the same companion set
as the previous 0.1.3 qualification, rather than claiming any future release.

The final 0.1.4 regression suite passes: 27 methods, with the external composed
startup method intentionally skipped there and run separately with actual matrix
outputs. The separate startup suite passes all three methods without skips: 56 positive
startup cases (8 standalone and 48 composed) plus the old-code negative control.
Each positive case completes six physics callbacks and reaches FMS status 44.
Both lookup API names are exercised with commands available immediately, at
flight start, on frame three, or never. The old-code control aborts at load.

Evidence and final counts are recorded under:
`/Users/wahltho/dev/intentional-fixes-startup-20261028/`.

These checks establish the corrected load-order behavior and source composition.
They do not establish flight, FPS, native-plugin integration or simulator acceptance.
