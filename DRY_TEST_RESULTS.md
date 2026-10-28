# Current startup repair — 0.1.4

See [STARTUP_REGRESSION_2026_10_28.md](STARTUP_REGRESSION_2026_10_28.md) for the
startup repair, 51 composition cases, 56 load-start cases and test limitations.
The 0.1.3 results below are historical.

# Dry-test results

Version 0.1.3 passes the final 23-method suite under both Lua 5.4 and LuaJIT,
all 576 FMS composition cases against released MTK 0.30.4/catalog 2.0.5,
six full-script LuaJIT loads and 204 composed-output component-method executions.
See [the current report](IMPLEMENTATION_0.1.3.md) for exact inputs and limits.
These are offline source/package checks, not simulator acceptance.

All results below apply to earlier source snapshots.

## Historical result — 2026-10-18

Source on 2026-10-18: **11/11 package, installer and focused behavior tests
PASS**, including I30 and I37-I39. All six behavior methods also pass under
LuaJIT. The standalone installed hash is verified by an executed lifecycle test.
The MTK 0.29.4/catalog 2.0.2 FMS source-composition matrix is **576/576 PASS**.
All six fully combined output scripts load under LuaJIT and pass six behavior
methods under both Lua 5.4 and LuaJIT: **72/72 method executions**, no skips.
Repeated composition uses MTK's verified-original contract. Full-aircraft MTK
installation/recovery, catalog qualification and simulator acceptance remain
open. See the
[current detailed report](DRY_TEST_RESULTS_2026_10_18.txt) for frozen inputs,
defect-sensitive controls, exact scope and remaining gates. No real aircraft,
distribution archive or public release has been changed by these tests.

Release follow-up: version 0.1.2 packages these same tested fix payloads. The
release-version bump and documentation edits are separate from the runs above;
all 18 payloads and the installer remain byte-identical to their frozen inputs.
Archive integrity and source equivalence are checked during packaging. This
does not add simulator evidence or MTK catalog qualification.

## Historical result — 2026-09-26

At the 2026-10-17 review, the I30 boundary defect was found after these checks.
The repair had not yet been dry-tested. The historical results below do not
validate its behavior or its new standalone result hash; use the current results
above for that repair. In
particular, Lua syntax acceptance did not detect the wrong first-intervention
scope; an executed full-handler regression case is required before release.

Final source snapshot result: **PASS (18/18 composition cases)**.

The test composed the package in memory after the selected functional modules,
using the verified original Zibo 4.05.35 Lua shared by current Zibo and LevelUp.
Each scenario was exercised with its original line format, normalized LF, and
CRLF plus BOM.

| Aircraft/input | Functional surface | Cases | Result |
|---|---|---:|---|
| Zibo 4.05.35 | clean | 3 | PASS |
| Zibo 4.05.35 | CPDLC 1.2 | 3 | PASS |
| LevelUp with shared .35 Lua | clean | 3 | PASS |
| LevelUp with shared .35 Lua | CPDLC 1.2 | 3 | PASS |
| LevelUp with shared .35 Lua | W&B 0.5.3 | 3 | PASS |
| LevelUp with shared .35 Lua | W&B 0.5.3 plus CPDLC 1.2 | 3 | PASS |

Every case verified exact structural application, the expected conditional
payload count, byte-identical second application, and successful `luac -p` of
the complete resulting `B738.a_fms.lua`. Regeneration of all payload documents
was byte-deterministic, and the source plan resolved exactly 18 families, 16
Lua-delta families, and 15 payload documents.

The first red runs exposed and the final source fixes close three package
defects: overlapping I24/I27 initializer contexts, two missing I05 function
closures, and one missing I30 outer ALT-INTV closure. I06 substitution contexts
were also widened so the exact-replacement engine can distinguish repeated
effective-response expressions during idempotent application.

This is source/package dry evidence only. MTK catalog/group integration, the
MTK repository's complete automatic suite, build, deployment and simulator
behavior were not run and are not claimed here.

The clean-.35 standalone installer additionally passes three focused lifecycle
tests: check/install/repeated-install/verify/uninstall with exact restoration,
rejection of a foreign edit before installation, and refusal to overwrite a
foreign edit after installation. The installed standalone result also passes
`luac -p` and matches its frozen result hash.
