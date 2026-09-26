# First-release candidate matrix

See `FIX_CATALOG.md` for the user-facing symptom and corrected-behavior
description of every family.

Status vocabulary:

- `source-ready`: exact structural payload authored;
- `analysis`: owner chain or target Lua block still being derived;
- `conditional`: payload must run only after a named functional module;
- `owner-blocked`: clean-Lua ownership is absent or not yet evidenced;
- `not-applicable`: the clean-Lua owner already rejects the failing state;
- `excluded`: not part of the unchanged-binary Lua package.

| Family | Scope | Status |
|---|---|---|
| I01 | GLS/LP record parsing, best match and LP vertical suppression | source-ready |
| I02 | TRUE/MAG course parse and single conversion | source-ready: shared I02/I03 owner payload |
| I03 | CI/VI stale/same-fix lookahead exclusion | source-ready: shared I02/I03 owner payload |
| I04 | Hold course, missing time/distance and dual-zero altitude semantics | source-ready |
| I05 | APP suffix/Ref-ICAO normalization and IF-preserving merge | source-ready |
| I06 | Existing datalink response/origin fallback | source-ready, conditional: CPDLC |
| I07 | PAUSE AT T/D context and rearm lifecycle | source-ready |
| I08 | Exact APP REF resolution using stock outputs | source-ready |
| I09 | Hold identity through route mutation | source-ready |
| I14 | Corrections to an installed CPDLC state machine only | source-ready: satisfied by selected CPDLC 1.2; no additional delta |
| I16 | Climb scope and neutral departure-role fail-closed behavior | source-ready |
| I24 | N1 manual/AUTO retirement and unavailable-OAT guard | source-ready |
| I27 | Manual go-around evidence owner | source-ready |
| I29 | Dashed SimBrief procedure placeholder normalization | not-applicable: shared clean .35 Lua validates SID/STAR/APP names and clears every non-match before import |
| I30 | Lower-MCP ALT INTV committed-constraint release | source-ready |
| I33 | Dynamic-station ZFW fail-closed behavior | source-ready, conditional: LevelUp W&B |
| I34 | Clean-descent rejoin VVI clamp | source-ready: bounded at the existing Lua VVI producer |
| I35 | T/D availability and commanded-descent guards | source-ready |

The first-release source ceiling is closed at 18 fix families: 16 families
have a Lua delta in 15 payload documents, I14 is inherited from CPDLC 1.2, and
I29 contributes no artificial no-op payload. Executed package, Lua-load,
functional and simulator validation remain open. I34 is gated at the existing
Lua producer by phase, path error, commanded demand and speed evidence; it is
not an unconditional clamp. The seven later owner candidates I15, I17,
I18, I25, I26, I28 and I31 are not part of the first source closure. The
eleven binary-bound families remain excluded.
