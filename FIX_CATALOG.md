# What's included

These fixes address existing FMS behavior in the original Zibo 4.05.35 Lua,
also used by LevelUp. They add no FMC pages, options or background services
and do not change `zibomod.xpl`.

The I-numbers are reference IDs used in the patch files and technical notes.

## Available with either installer

These 14 fixes are included with both Toolkit installation and the
clean-.35 standalone installer.

### I01 — GLS, LPV and LP approach data

Navigation records can encode approach type, course and glideslope in different
ways. The fix reads these variations and selects the matching runway and
course record. It also prevents a lateral-only LP approach from showing
vertical guidance as though it were LPV.

### I02 — True and magnetic procedure courses

Some procedure courses use a `T` suffix for true north; others are stored in
tenths of a degree. Incorrect scaling or repeated magnetic-variation
corrections can make the FMC, ND and flown leg disagree. The fix reads the
units and north reference consistently and converts the course once where
needed.

### I03 — Course and heading intercepts

During route edits, deleted or duplicate legs can remain in the temporary
route data. CI/VI intercept calculations could use one of these instead of
the intended next leg. The fix skips those entries when choosing the intercept
target and handles the first-leg boundary safely.

### I04 — Hold courses, altitude and leg length

An entered magnetic hold course could receive an extra magnetic-variation
correction. Holds could also show the wrong true/magnetic reference,
misinterpret an exact altitude restriction, or become zero miles long when
navdata omitted both time and distance. The fix corrects these cases and uses
the existing default length when the published length is missing.

### I05 — Approach names and initial fixes

Approach names with Y/Z suffixes can display inconsistently. Reference-airport
lookup could also read the wrong approach entry. Both are corrected without
changing the selected procedure. When approach legs are joined or cleaned up,
a published initial fix (IF) is kept as an IF rather than changed to a
track-to-fix (TF) leg.

### I07 — PAUSE AT T/D

The existing PAUSE AT T/D option could remain armed or trigger without a
usable top-of-descent point. The fix checks the active cruise route and T/D
before pausing and resets the pause state so it can work again when appropriate.

### I08 — APP REF data

An ambiguous runway or ILS/LDA lookup could select the wrong record or leave
APP REF values drawn from different records. The fix uses the matching runway
and approach record for the existing APP REF values.

### I09 — Holds after route changes

EXEC, route activation, Direct and offset changes could turn a hold leg into
an ordinary route leg or lose its identity as a manual or procedure hold.
The fix preserves that identity through those changes and prevents offset
updates from overwriting the hold.

### I16 — Climb restrictions

The FMS could scan beyond the climb portion of a route and pick up speed or
altitude restrictions from an arrival or approach. The fix stops the climb
scan at those boundaries and at a discontinuity. Restrictions for an active
missed approach are handled separately.

### I24 — Manual N1 and missing OAT

Manual N1 could be cleared by a flight-phase change or by arming VNAV, even
without an engaged-autopilot vertical-mode change. The fix uses the actual
vertical-mode change for that decision. It also leaves the FMC N1 reference
unavailable on the ground when a non-aspirated aircraft requires an entered
OAT and none has been entered. The existing N1 bug parking position is retained.

### I27 — Manual go-around detection

Flap position, thrust and AP state alone could make the FMS infer a go-around
without a go-around sequence. The fix requires an observed retraction from
landing flap during the same arrival and resets that record between arrivals.

### I30 — ALT INTV and altitude restrictions

With a lower MCP altitude selected, ALT INTV could miss the intended
restriction because of its altitude threshold or affect the wrong route data.
The fix releases the next conflicting altitude restriction on the active route
and protects pending MOD edits. The existing DES NOW behavior is retained.

### I34 — Rejoining the descent path

Below the descent path, with a commanded descent, the aircraft clean and
airspeed at or below target, the FMS could demand an excessive descent rate
to rejoin the path. The fix limits that demand under those conditions.
Other descent modes and high-speed cases keep their existing behavior.

### I35 — Incorrect descent phase changes

A missing or passed T/D could be taken as sufficient reason to enter descent,
including during initialization or a go-around. V/S or LVL CHG could also
count as descent while targeting a higher altitude. The fix checks these cases
before changing flight phase and requires a lower selected altitude for
V/S or LVL CHG descent.

## Applied by the Toolkit when the relevant module is selected

### I06 — CPDLC replies

Some PDC/CLD clearance messages arrive without a response code. The fix
recognizes these messages and makes WILCO available consistently. If the logon
target has been cleared, it uses the current uplink's origin for the reply.
It also handles missing route information in PREDEP messages.

Requires the CPDLC module. The standalone installer does not include this fix.

### I33 — LevelUp automatic ZFW

With the LevelUp W&B module, missing or invalid payload-station data could
produce a plausible but incorrect automatic ZFW using the old crew-weight
calculation. The fix checks the aircraft and station data first. If the data
is invalid for a recognized LevelUp aircraft, automatic ZFW is shown as
unavailable instead of using that fallback.

Requires LevelUp W&B. The standalone installer does not include this fix.

## Reviewed items that need no additional patch

### I14 — CPDLC message handling

The reviewed reply, retry and completion fixes are already included in
CPDLC 1.2. Intentional Fixes does not install them a second time.

### I29 — SimBrief procedure placeholders

The original .35 Lua already checks imported SID, STAR and approach names
against the available procedures and clears non-matches, including dashed
placeholders. No additional change is included for this item.

## Verification and support

The automated tests check installation and Lua syntax. They are not flight
tests; see [DRY_TEST_RESULTS.md](DRY_TEST_RESULTS.md) for the tested combinations.

This is an unofficial patch, not supported by Zibo, LevelUp or Laminar
Research. For help or to report a problem, use the
[wahltho Discord server](https://discord.gg/ySS88PMuyC).

Only the items described above are covered by this release. Other proposed
Lua fixes and fixes that would require binary changes are not included.
