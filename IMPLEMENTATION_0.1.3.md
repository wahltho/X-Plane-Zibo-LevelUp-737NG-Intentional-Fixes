# Intentional Fixes 0.1.3: implementation and dry checks

Status: final automatic source/package checks PASS for release 0.1.3.
The GitHub tag and release record publication. No aircraft deployment or
simulator command was performed in this implementation round.

## Scope and ownership

I02 is a repair of the existing course-decoding patch. I40 is the new VI and
ground-LNAV fix. Both are in the common Lua patch source used by standalone and
MTK. No changes were made to the C++ port, original Lua, original plugin binary,
MTK source repository or installed aircraft.

The target remains the exact original .35 FMS Lua, shared by Zibo and LevelUp:
`ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e`.
Final standalone result:
`233ec98c96cfd3c0ac171583882b1e6d39da83bdc9f4a7e4d190e1cc6e41f48f`.
The source repository started clean on main at
`5555ba6ef8c35be6e6bef549316521a9d19efaeb`.

The package has 22 catalog families, 20 with a Lua delta in 19 payload
files. Standalone includes 18 families in 17 files. I06 remains conditional on
CPDLC and I33 on LevelUp W&B; I14 and I29 require no additional payload.
Existing module order remains functional patches → Intentional Fixes → Lua Timer.

## Separate repairs

I02 reads four-digit magnetic values in tenths, three-digit `T` values in whole
true degrees, and the existing numeric HOLD forms separately. Zero is a valid
north course; missing or malformed input is unavailable. It preserves raw29.
FD/FC/FM conversion uses the original start-point finder within a scope that
restores XLua namespace state on success or error. PI uses its resolved fix.
Borrowed magnetic radial operands retain the original declination expression.
AF/RF computed geometry is not replaced with prescribed-course semantics.

The I03 successor selection and first-leg guard remain in place. The selected
buffer count is used for its lookahead. I04 keeps published HOLD time values
such as `T010`, and defaults only a genuinely missing numeric distance.

I40 separates prescribed VI heading from geometry track. It refreshes private
VI source course before coordinate-cache admission, after coherent route copies,
and after complete plugin geometry feedback. It never invents coordinates,
changes a geometry-validity flag, or converts an unavailable course into north.

Native publication retains its own VI source image. A real ACT mutation retires
the private-route match before the write, while the last exported intent remains
available to repair both native magnetic VI operands at their current exported
endpoint. The completion callback acknowledges the scalar command; count-only
notification does not consume an unfinished packet. Geometry adoption validates
the entire packet and refreshes dependent VI rows after all coordinates are
adopted, independently of packet ordering. Ordinary distance sampling does not
retire a valid publication.

Ground arming uses the literal first committed departure leg. For VA/VD/VI/VM/VR,
it compares the prescribed heading and the actual runway direction within
5 degrees in a common true reference. Non-V legs keep the existing geometric
track comparison. It refreshes on normal callbacks, completed ACT export and
command phase zero, including while MOD work is busy. It does not engage an AP
mode, change an FMA, skip to a later V leg, or invent runway geometry.

## Closure matrix

| Surface | Source result | Automatic evidence / limit |
|---|---|---|
| Raw course format, units, north, invalid values | Explicit typed reader; immutable raw29 | Parser/component cases; not flight proof |
| Own decoder classes and start datum | Eleven raw groups repaired; FD second lookup retains predecessor; PI deferred | Whole-decoder components with bounded I/O/geometry stubs |
| CI/VI borrowed operands, AF/RF policy | I03 and geometric ownership preserved | Independent source review; selected decoder boundaries |
| LEGS, PROGRESS, HOLD, track readers | ACT versus MOD buffer and reference datum retained | Source review; no full FMC visual acceptance |
| Five native publisher pairs | Degrees/radians written consistently at native endpoint | Source review and source-wiring checks |
| VI mutation, copies and publication lifecycle | Actual ACT writers guarded; source image retained separately | Source-owner inventory plus component tests; no continuous aircraft replay |
| Plugin completion, ACK, count, feedback | Completed packet validation and dependent-row refresh | Callback/reader components including busy MOD and retired ACT |
| Ground heading/runway/reference/5-degree boundary | Literal first V-heading and real runway record | Wrapped boundary and MAG/TRUE component cases |
| MTK optional-module combinations | Exact anchors preserve earlier modules | PASS: 576/576 released-handler cases; bounded FMS scope |
| Standalone lifecycle | Strict clean .35 source and fixed 17-payload guard | PASS: exact install/check/repeat/uninstall and foreign-edit rejection |
| LuaTimer cache contract | Key, age, finite/admission and reuse unchanged | Composition and source review; no performance/runtime claim |

`src/vi-mutation-owners.json` records the concrete guarded source owners.
The four `.lua` files under `src/` are authoring assets inserted into the existing
FMS module. They are not separate XLua modules installed into the aircraft.

## Independent review

Both independent read-only reviewers gave bounded source-review GO on composed
hash `9661cbf8bbbe7cb0b4c91d85a51779b66dea265bab58f9b5e1a48eec6e545eed`.
The next snapshot preserved one original trailing blank CRLF. The final snapshot
also moves flight_start retirement across its blank line to anchor before the
original latitude/longitude pair. The publication/lifecycle reviewer verified
these exact differences and extended bounded source-review GO to the final hash.
W&B and 27K entry resets only touch their private metadata/datarefs; retirement
still precedes the original lifecycle writes.

The accepted pre-test findings covered XLua namespace restoration, ground gate
refresh at export commit, early VI source save, FD's second query, PI's resolved
fix, unavailable-input guards and refresh-before-return ordering.

## Tests

The final 23-method package, installer and component suite passed under both
Lua 5.4 (134.659 s) and LuaJIT (134.890 s), with no skips. Logs are
`unittest-lua54-release.log` and `unittest-luajit-release.log`. This includes the I30 whole-handler cases, I37–I39,
I02/I40 and a running-X-Plane rejection case. The test CLI restricts its target
to a disposable temporary aircraft and stubs only process inventory; the
production process guard is unchanged. The initial unisolated lifecycle round
was correctly blocked by the running simulator; X-Plane was left untouched.
The released-handler matrix passes all 576 cases: 64 Zibo and 128 LevelUp
optional selections in each of the original, LF and CRLF+BOM formats. The
canonical driver was run in three independent line-format slices; only its
line-format loop was restricted in each copy. All product/format/mask IDs were
verified exactly once. The real released Core was neither rebuilt nor changed.
Clean-baseline recomposition and all-selected Intentional Fixes reapplication
are byte-identical; the existing whole-pipeline W&B rejection and catalog
provenance rejection remain effective. Every resulting script passes luac.
The six fully combined scripts also load under LuaJIT and pass 17 component
methods under both Lua 5.4 and LuaJIT: 204 method executions, no skips. These
method counts include inherited cruise methods; they are not unique scenarios.

Evidence root:
`/Users/wahltho/dev/intentional-fixes-dry-20261027.309w22l2/`.
Current published MTK inputs are pinned to Core 0.30.4 / catalog 2.0.5.
The exact archive, Core and catalog SHA-256 values and every companion release
are recorded in `mtk-wb-final/input-pins.json`. LuaTimer helper
`95096d0a476fbb33f793290e2762c69187ce86894ec4723549c78362713eb64f`
retains its four-coordinate key (including signed zero), 0.05-second age bound,
finite admission, exception invalidation and existing miss-based disable rule.
No added ACT writers were found in the published companion insertions and
replacements, including the separate VNAV table payloads.
The final matrix inputs and results are under `mtk-wb-final/`.

The initial matrix exposed exact text anchors that included unrelated CPDLC or
VREF changes. The author now widens only an ambiguous hunk instead of widening
all hunks to the same large context. The exact-handler checks remain strict.
A second anchor round exposed 27K/SFP entry code at `flight_start`; pure
function-entry hooks now anchor only their unique declaration and preserve
other modules’ entry blocks. W&B also annotates the flight_start declaration;
that one hook now anchors the unchanged latitude/longitude pair instead. Both
all-selected product preflights pass with this final anchor. The standalone
test golden hash was updated for the reviewed blank-line movement. A separate
installer round exposed the old
16-payload count guard, now 17.
Two early course fixtures lacked nav-query/intersection stubs; their correction
changed test fixtures only. None of these initial rounds is reported as a final
passing result.

## Relation to the LGSK report and open boundaries

The local LGSK/01 EVIK1E and EVIK1B CIFP records contain magnetic course tokens
including `0140` and `0130`. The whole-decoder component checks use these exact
tokens and require 14 and 13 degrees respectively; the published I02 payload is
a defect-sensitive negative control. This identifies the I02 scaling regression
class. It does not establish that the forum reporter used the same AIRAC, that
the complete SID has been replayed, or that every reported symptom is fixed.

Native non-VI TRUE coherence, especially TRUE-HOLD, remains open. The unchanged
binary has consumers with different conversion datums and no proven Lua boundary
that repairs that complete contract. Native handling of unavailable intercept
geometry is likewise not claimed fixed. The .31 reconstruction is not proof for
the .35 binary; the bounded .35 native receipts concern the original Linux build,
not complete Windows/macOS or runtime acceptance.

These are source/package and stubbed component checks. No complete continuous
flight replay, full-aircraft MTK install/rollback/recovery, catalog release
qualification, simulator acceptance or resolution of the reported flight is
claimed. Publication is a source/package release, not additional flight evidence.
