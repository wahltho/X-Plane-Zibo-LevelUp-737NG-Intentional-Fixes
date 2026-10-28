# Patch coverage — 0.1.4

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
| I02 | Declared MAG tenths/TRUE whole degrees, start-datum projection, unchanged raw token | repaired; automatic checks PASS; shared I02/I03 owner payload |
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
| I30 | Lower-MCP ALT INTV committed-constraint release | source-ready; repaired boundary/fallback regressions dry-tested, not whole-domain certification |
| I33 | Dynamic-station ZFW fail-closed behavior | source-ready, conditional: LevelUp W&B |
| I34 | Clean-descent rejoin VVI clamp | source-ready: bounded at the existing Lua VVI producer |
| I35 | T/D availability and commanded-descent guards | source-ready |
| I37 | Passed waypoint exclusion in secondary CRZ speed scan | included in 0.1.2; focused behavior and FMS composition PASS |
| I38 | Both FMC CRZ LSK2 handlers reject edits to a displayed MCP target | included in 0.1.2; focused behavior and FMS composition PASS |
| I39 | W/STEP arrival-fuel sign and display-unit conversion | included in 0.1.2; focused behavior and FMS composition PASS |
| I40 | VI prescribed heading, native feedback/publication lifetime, ground V-heading arming within 5 degrees | source/package checks PASS; native non-VI TRUE/HOLD and full flight resolution remain open |

Version 0.1.4 contains 22 catalog families, 20 with Lua changes in 19
payload documents. Standalone includes 18 families in 17 payload documents.
I02 remains a separate repair from I40. Where their exact installed signatures
share a Lua block, that block includes both changes to preserve reapplication.
I30's only additional change is I40's active-route retirement guard around its
existing writes. See [the test report](IMPLEMENTATION_0.1.3.md).

## Historical 0.1.2 results

The first release contained 18 fix families in 15 payload documents. The
0.1.2 release adds I37-I39: 21 families, 19 with a Lua delta in 18 payload
documents. I14 is inherited from CPDLC 1.2, and I29 needs no artificial no-op
payload. The standalone source includes 17 families in 16 payload documents.
The corrected I30 and new payloads pass the 11-method package/component suite,
576 released-MTK FMS composition cases, six complete-script LuaJIT loads and
72 composed-output behavior executions. See `DRY_TEST_RESULTS_2026_10_18.txt`
for exact scope and the corrected MTK repeat contract. Full-aircraft MTK
installation/recovery, catalog qualification and simulator acceptance remain
separate. I34 is gated at the existing
Lua producer by phase, path error, commanded demand and speed evidence; it is
not an unconditional clamp. The seven later owner candidates I15, I17,
I18, I25, I26, I28 and I31 are not part of the first source closure. The
eleven binary-bound families remain excluded.

I36 is reserved by the port inventory for an AP-consumer change requiring a
binary modification; it is not a missing Lua payload. See
`CRUISE_FIXES_REVIEW_2026_10_18.txt` for the I37-I39 scope and MTK source audit.
