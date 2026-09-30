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
| Clean-only standalone result | `49a6ab1f077bca893123f476873ec5e7c9af1d18e31570996a697403ae2c3f70` |

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

I02 and I03 share a patch file. The 14 unconditional fixes use 13 patch files.
I06 applies after CPDLC 1.2; I33 applies after LevelUp W&B 0.5.3.
I14 is already included in CPDLC 1.2, and I29 is already handled by the original
.35 Lua. Neither needs an additional patch. The standalone installer includes
only the unconditional fixes.

The Toolkit applies selected functional modules before Intentional Fixes.
Unknown or incompatible input is rejected rather than patched by guesswork.

## MTK package

The separate 0.1.1 MTK archive can be generated with:

```text
python3 tools/build_mtk_package.py --check --archive <output.zip>
```

It uses schema 5 and requires Toolkit 0.21.1 or newer. The Zibo module excludes
I33. The LevelUp module applies I33 only when Weight & Balance is selected.
Both modules apply I06 only when CPDLC is selected.

This archive is separate from the standalone 0.1.0 installer and contains no
complete aircraft Lua file.

## Checks performed

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
