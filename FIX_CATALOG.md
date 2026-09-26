# Intentional Fixes catalog

This package corrects existing Zibo 4.05.35 Lua behavior. It adds no FMC page,
user option, background service or new operational feature, and it never
changes `zibomod.xpl`. The current Zibo and LevelUp aircraft use the same clean
.35 Lua baseline.

The Maintenance Toolkit selection covers 18 reviewed fix families. Fourteen
families are unconditional and are also available in the clean-.35 standalone
installer. I06 and I33 are conditional corrections for selected functional
modules. I14 is already satisfied by CPDLC 1.2, and I29 is already satisfied
by the clean .35 baseline, so neither receives an artificial no-op payload.

## At a glance

| ID | Area | Corrected behavior | Clean standalone |
|---|---|---|:---:|
| I01 | GLS/LP navdata | Robust record parsing and best-match selection; LP remains lateral-only | Yes |
| I02 | Procedure courses | TRUE/MAG and tenth-degree values are parsed and converted exactly once | Yes |
| I03 | CI/VI intercepts | Stale or same-fix preview legs cannot become the intercept lookahead owner | Yes |
| I04 | Holds | Correct course reference, altitude semantics and missing time/distance defaults | Yes |
| I05 | Approaches | Canonical APP display, correct Ref-ICAO row and IF-preserving merge | Yes |
| I06 | CPDLC replies | Missing response codes and lost origin/route context fail over safely | CPDLC only |
| I07 | PAUSE AT T/D | Pause is armed only for a valid active cruise/T/D context and rearms correctly | Yes |
| I08 | APP REF | Exact runway/ILS/LDA reference resolution with coherent stock outputs | Yes |
| I09 | Holds/route edits | Hold identity survives EXEC, Direct, activation and offset mutations | Yes |
| I14 | CPDLC lifecycle | Corrected CPDLC 1.2 state-machine behavior is recognized, not duplicated | CPDLC 1.2 |
| I16 | VNAV climb | Climb restrictions cannot leak into arrival, approach or discontinuity domains | Yes |
| I24 | N1 | Manual/AUTO ownership retires on the correct event; missing OAT fails unavailable | Yes |
| I27 | Go-around phase | Manual go-around requires observed landing-flap retraction evidence | Yes |
| I29 | SimBrief import | Invalid dashed procedure placeholders are already rejected and cleared | Already safe |
| I30 | ALT INTV | The next conflicting committed altitude constraint is released correctly | Yes |
| I33 | LevelUp W&B | Invalid live station geometry cannot publish a plausible automatic ZFW | W&B only |
| I34 | VNAV descent | Clean-descent path rejoin demand is bounded when speed is not high | Yes |
| I35 | Flight phase | Missing/crossed T/D and non-descending modes cannot falsely force descent | Yes |

## Detailed descriptions

### I01 — GLS/LP record resolution

**Problem:** Earth-nav Type 14 records can use different service, course and
glideslope encodings. A weak match can select the wrong runway/course record,
and an LP service can be treated as though it supplied LPV-style vertical
guidance.

**Correction:** Parse LP, LPV and GLS variants tolerantly, retain the approach
identifier, select the best runway/course match, and keep vertical deviation
off-scale for lateral-only LP service.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I02 — TRUE/MAG course ownership

**Problem:** CIFP course fields may carry a `T` suffix or use tenth-degree
units. Scaling or applying magnetic variation more than once can make the FMC,
ND and flown leg disagree.

**Correction:** Parse the published representation once, preserve the true
reference where needed, convert once at the local leg position, and publish a
consistent magnetic course to downstream stock consumers.

**Delivery:** Unconditional; shares one owner payload with I03.

### I03 — CI/VI intercept lookahead

**Problem:** During route editing, stale, deleted or same-fix duplicate preview
rows can be selected as the next leg for CI/VI intercept geometry.

**Correction:** Skip non-owning preview rows before decoding the intercept
target, including a safe boundary check before the first leg.

**Delivery:** Unconditional; shares one owner payload with I02.

### I04 — Hold course and default semantics

**Problem:** Hold entries can be double-converted for magnetic variation,
display the wrong TRUE/MAG reference, interpret an exact altitude incorrectly,
or create a zero-mile hold when CIFP supplies neither time nor distance.

**Correction:** Store entered magnetic courses directly, display published
true courses where appropriate, recognize dual-zero "at" altitude semantics,
and use the bounded stock hold default only when the source value is actually
missing.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I05 — Approach identity and IF-preserving merge

**Problem:** Y/Z approach suffix variants can display inconsistently, Ref-ICAO
parsing can use the wrong APP row, and procedure merge/cleanup can degrade a
published IF leg to TF at a common-final or procedure-intercept join.

**Correction:** Canonicalize the displayed approach identifier without changing
the selected procedure, bind Ref-ICAO parsing to the selected row, and preserve
IF semantics through both route variants and merge paths.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I06 — CPDLC effective response and origin fallback

**Problem:** Some existing PDC/CLD uplinks lack an explicit response code, and
their logon origin or secondary PREDEP route context may disappear before a
reply is sent or rendered.

**Correction:** Infer WILCO only for recognizable existing PDC/CLD messages,
use that effective response consistently, answer the current uplink origin if
the logon target was cleared, and keep PREDEP route context nil-safe.

**Delivery:** Conditional MTK correction after CPDLC; excluded from standalone.

### I07 — PAUSE AT T/D lifecycle

**Problem:** The option can remain armed or trigger without a valid active
cruise route and usable T/D context.

**Correction:** Bind arming, triggering and rearming to the current active
cruise/T/D lifecycle while retaining the existing user option and behavior.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I08 — Exact APP REF resolution

**Problem:** Ambiguous runway or ILS/LDA lookup can combine reference values
from neighboring records or leave incoherent stock APP REF outputs.

**Correction:** Resolve the exact applicable runway/approach record and update
the existing stock APP REF values as one coherent result. No new external API
or FMC page is added.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I09 — Hold identity through route mutation

**Problem:** EXEC, route activation, Direct and offset synchronization can
temporarily rewrite HA/HF/HM hold rows as ordinary DF/TF geometry, losing the
manual or procedure hold identity.

**Correction:** Recognize hold context from the surrounding stock route rows,
rebuild hold ownership after mutations, arm manual-hold interception without
rewriting the hold, and prevent offset synchronization from splicing over it.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I14 — CPDLC state-machine corrections

**Problem:** An incomplete CPDLC transaction/lifecycle owner can leave message
state inconsistent across reply, retry or completion paths.

**Correction:** The supported CPDLC 1.2 module already contains the reviewed
corrected state-machine behavior. Intentional Fixes records that closure and
does not apply a duplicate or competing Lua block.

**Delivery:** Satisfied when CPDLC 1.2 is selected; no standalone payload.

### I16 — Climb-restriction domain boundary

**Problem:** A climb speed or altitude restriction scan can continue into
arrival, approach or discontinuity rows and publish a constraint from the
wrong route domain.

**Correction:** Bound the scan to climb and neutral departure roles, stop
fail-closed at arrival/approach/discontinuity boundaries, and preserve the
separate active missed-approach climb domain.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I24 — N1 mode retirement and OAT availability

**Problem:** Manual N1 can retire on flight-phase or VNAV-arm proxies instead
of a real engaged-AP vertical-mode change. On the ground, a non-aspirated
aircraft can also publish a plausible N1 reference without entered OAT.

**Correction:** Use the existing normalized AP vertical-mode publication as
the retirement owner, and publish N1 unavailable when required ground OAT is
missing. The aircraft model's existing bug-park position is retained.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I27 — Manual go-around evidence

**Problem:** A static combination of flap, thrust and AP state can be mistaken
for a manual go-around and change FMC phase outside a real go-around sequence.

**Correction:** Require observed same-arrival landing-flap retraction as the
transition evidence, with lifecycle state that cannot leak between arrivals.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I29 — Dashed SimBrief procedure placeholders

**Problem:** SimBrief may supply dashed or otherwise invalid SID, STAR or APP
placeholder names.

**Correction:** The shared clean .35 Lua already validates every imported
procedure name against its list and clears each non-match before rebuilding the
route. Adding a no-op patch would reduce safety rather than improve it.

**Delivery:** Baseline-satisfied; no payload in MTK or standalone.

### I30 — Lower-MCP ALT INTV constraint release

**Problem:** Lowering the MCP and pressing ALT INTV can use deadbands or broad
deletion loops, miss the intended constraint, or alter MOD-owned data while
trying to release the active route.

**Correction:** Find and release exactly the next conflicting committed
altitude constraint in the valid climb/descent domain, mirror only an unchanged
stock route copy, and preserve the existing DES NOW transition semantics.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I33 — LevelUp W&B automatic ZFW gate

**Problem:** Missing, invalid or incompatible live station geometry can fall
back to legacy crew arithmetic and publish a plausible but incorrect automatic
ZFW.

**Correction:** Validate the complete current LevelUp aircraft/station contract
before using physical station mass. A known LevelUp aircraft with an invalid
contract fails unavailable instead of falling back silently.

**Delivery:** Conditional MTK correction after LevelUp W&B; excluded from standalone.

### I34 — Clean-descent rejoin demand

**Problem:** During a clean descent below path, the stock rejoin producer can
command excessive downward VVI even when airspeed is at or below target.

**Correction:** Bound the existing VVI producer only in the proven clean,
below-path, commanded-descent and non-high-speed case. High-speed energy
management and other descent modes retain their existing authority.

**Delivery:** Unconditional; included in MTK and clean standalone.

### I35 — Flight-phase descent guards

**Problem:** A missing or crossed T/D, phase-zero initialization, go-around, or
an upward V/S/LVL CHG target can be misread as evidence that descent owns the
flight phase.

**Correction:** Treat missing T/D as unknown rather than descent, preserve
initialization and go-around ownership, and require a genuinely lower selected
target before V/S or LVL CHG counts as commanded descent.

**Delivery:** Unconditional; included in MTK and clean standalone.

## Package boundaries

- Clean standalone: 14 corrective families in 13 payload documents.
- MTK with no functional CPDLC/W&B module: the same 14 corrective families.
- MTK with CPDLC 1.2: adds conditional I06 and recognizes I14 as already satisfied.
- MTK with LevelUp W&B: adds conditional I33.
- I29 remains documented baseline behavior in every combination.
- Seven later Lua-owner candidates and eleven binary-owned families are outside
  this first release; they are not silently included or advertised as fixed.
