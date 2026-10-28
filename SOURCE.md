# Source and compatibility record

This package applies text patches to:

`plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua`

It does not distribute that complete file and does not modify or distribute
`zibomod.xpl`.

## Clean baseline

The standalone installer accepts only the untouched original Zibo 4.05.35 Lua:

| Input | SHA-256 |
|---|---|
| Original Zibo 4.05.35 `B738.a_fms.lua` | `ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e` |
| LevelUp repository copy checked on 2026-09-26 | `ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e` |
| Published 0.1.0 standalone result | `49a6ab1f077bca893123f476873ec5e7c9af1d18e31570996a697403ae2c3f70` |
| Historical intermediate I30-only result (not released) | `01bf0a2c2cd873c8880cafed4e3925412afb26c02b4ded57b1e4f46d0e1299de` |
| Version 0.1.2 standalone result (I30 + I37-I39) | `48e000794942a37ae661a80f52d2d099b4469528825e42871503e57ca2d2d444` |
| Version 0.1.3 standalone result (I02 repair + I40) | `233ec98c96cfd3c0ac171583882b1e6d39da83bdc9f4a7e4d190e1cc6e41f48f` |
| Version 0.1.4 standalone result (deferred LNAV registration) | `0e2d97a64e985801b0a9b460bfcc430ed32a1510c05c6432a928f23021323898` |

The two input files were byte-identical when checked. The LevelUp product
version is not a separate Lua baseline for this release.

## How the patches were prepared

Each patch contains the original text needed to locate the change and the
replacement text. The changes were adapted from the reviewed last-active Lua
and related investigations, keeping only fixes that can work with the
unchanged original binary.

[FIX_CATALOG.md](FIX_CATALOG.md) describes the problems and corrections.
[PATCH_MATRIX.md](PATCH_MATRIX.md) records the technical status.
`package-plan.json` defines application order and module requirements.

I02 and I03 share a patch file. The 0.1.3 release’s 18 unconditional families
use 17 patch files. Authoring helpers under `src/` are inserted into the
existing FMS module; they are not separately installed XLua scripts.
I06 applies after CPDLC 1.2; I33 applies after LevelUp W&B 0.5.3.
I14 is already included in CPDLC 1.2, and I29 is already handled by the original
.35 Lua. Neither needs an additional patch. The standalone installer includes
only the unconditional fixes.

The Toolkit applies the earlier functional modules before Intentional Fixes.
The current catalog places Lua Timer afterwards (order 90); its anchors are
unchanged. No module order or dependency has been altered by these additions.
Unknown or incompatible input is rejected rather than patched by guesswork.

I37-I39 are bounded changes to the original Lua, not copies of the port's
planner or page architecture. See [the source review](CRUISE_FIXES_REVIEW_2026_10_18.txt)
for the original blocks, port evidence, existing MTK hooks and open test gates.

## MTK package

The separate MTK archive can be generated with:

```text
python3 tools/build_mtk_package.py --check --archive <output.zip>
```

It uses schema 5 and requires Toolkit 0.21.1 or newer. The Zibo module excludes
I33. The LevelUp module applies I33 only when Weight & Balance is selected.
Both modules apply I06 only when CPDLC is selected.

This archive is separate from the standalone installer and contains no
complete aircraft Lua file. It must be qualified and offered by the MTK catalog
before managed installation; archive publication does not update that catalog.

## Checks performed

The 0.1.3 source and test report is
[IMPLEMENTATION_0.1.3.md](IMPLEMENTATION_0.1.3.md). The 0.1.2 results below
are historical; the 0.1.3 report records the new final-source runs. The .35 binary evidence
used to bound I40 is from the original Linux build; the .31 reconstruction
does not prove .35 behavior on every platform. Native non-VI TRUE/HOLD
coherence and the reported flight's complete resolution remain open.

Version 0.1.2 includes the I30 boundary correction and I37-I39 additions.
The 11-method package, installer and focused behavior suite passes, including
exact standalone restoration and defect-sensitive I30/I37-I39 cases. The six
behavior methods also pass under LuaJIT. All 576 FMS composition cases against
published MTK 0.29.4/catalog 2.0.2 pass, along with six complete-script LuaJIT
loads and 72 behavior method executions on fully combined outputs. Repeated
composition follows MTK's verified-original contract. Full-aircraft MTK
installation/recovery, catalog release qualification and simulator acceptance
remain open; see the [current report](DRY_TEST_RESULTS_2026_10_18.txt).

The dry tests ran before the release-version bump. Release preparation changes
package versions and documentation, not any of the 18 fix payloads or the
installer. Their hashes are checked against the frozen dry-test inputs; the
576-case matrix is not claimed as a new run on the versioned release archives.

[DRY_TEST_RESULTS.md](DRY_TEST_RESULTS.md) records the patch-application,
repeat-application, line-ending, restoration and Lua-syntax checks. These
checks do not establish simulator behavior.

This is an unofficial package. Zibo, LevelUp and Laminar Research do not
provide support for it. Support is through the
[wahltho Discord server](https://discord.gg/ySS88PMuyC).

## License

The MIT license applies to the original installer, authoring/release tools,
patch definitions, tests and documentation in this repository. It does not
relicense upstream aircraft code. Product names identify compatible aircraft;
they do not imply endorsement.
