# Source and compatibility record

This independent package applies bounded exact-text corrections to one file:

`plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua`

It does not distribute that complete file and does not modify or distribute
`zibomod.xpl`.

## Clean baseline

The standalone installer accepts only the untouched original Zibo 4.05.35 Lua:

| Input | SHA-256 |
|---|---|
| Original Zibo 4.05.35 `B738.a_fms.lua` | `ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e` |
| Current LevelUp repository copy | `ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e` |
| Clean-only standalone result | `49a6ab1f077bca893123f476873ec5e7c9af1d18e31570996a697403ae2c3f70` |

The two input rows were verified byte-identical on 2026-09-26. The LevelUp
product version is not a second Lua baseline for this release.

## Patch derivation

Each payload contains only the exact original context required to identify its
owner and the corresponding corrected block. The fixes were reconciled from
the reviewed last-active Lua behavior and the integrated owner-chain findings,
then reduced to fix-only Lua changes that remain valid with the unchanged
original binary. `FIX_CATALOG.md` describes every included invariant;
`PATCH_MATRIX.md` records the source-closure classification.

I06 targets the completed CPDLC 1.2 surface and I33 targets the completed
LevelUp W&B 0.5.3 surface. I14 is already satisfied by CPDLC 1.2. I29 is
already satisfied by clean .35 and therefore has no no-op payload. The
standalone installer deliberately excludes every conditional family.

## Validation boundary

The final source passes the composition, idempotence, line-ending and Lua
syntax dry matrix recorded in `DRY_TEST_RESULTS.md`. These checks do not claim
simulator-runtime validation. The package is unofficial and independent;
support is not provided by Zibo, LevelUp or Laminar Research.

## Licensing boundary

The MIT license applies to the original installer, authoring/release tools,
declarative patch design, tests and documentation in this repository. It does
not relicense any complete upstream aircraft file. Upstream product names are
used only for compatibility identification.
