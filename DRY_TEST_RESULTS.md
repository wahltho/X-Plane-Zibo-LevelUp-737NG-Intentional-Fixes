# Dry-test result — 2026-09-26

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
