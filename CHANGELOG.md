# Changelog

## 0.1.4 — 2026-10-28

- Fix an I40 startup-order error: wait for the native LNAV command before
  registering its wrapper, retrying from lifecycle callbacks if needed.
- Prevent duplicate registration and stop command lookups after success.
- Preserve existing fix behavior, module selection and installation ownership.
- Verify Zibo/LevelUp composition and offline startup with companion patches,
  including delayed and unavailable commands. Simulator validation remains open.

## 0.1.3 — 2026-10-27

- Repair I02 course decoding: read magnetic values as tenths and `dddT` as
  whole degrees true. Keep the original course token unchanged and use the
  appropriate start point for conversion. Preserve I03 intercept lookahead.
- Preserve published HOLD time tokens such as `T010` when applying I04 defaults.
- Add I40: keep a VI's prescribed heading separate from calculated track;
  correct both native VI course operands after geometry feedback; reject
  feedback for a retired active-route publication.
- Ground LNAV arming compares the first prescribed V-heading with the actual
  departure runway direction within 5 degrees, using a common north reference.
- Include the same repair and I40 in standalone and MTK source definitions:
  22 catalog items, 20 Lua-delta families, 19 payload documents; standalone
  18 families in 17 payload documents. No new aircraft pages or options.
- This release does not establish resolution of the reported LGSK flight.
  Native non-VI TRUE/HOLD coherence remains outside the Lua repair.

## 0.1.2 — 2026-10-18

- Fix the I30 replacement boundary: ALT INTV constraint deletion is no longer
  inside the first-intervention gate, and the original cruise-altitude fallback
  is retained. Update standalone and MTK payload metadata accordingly.
- Add I37: prevent already-passed waypoint speed restrictions from returning
  as cruise speed targets.
- Add I38: reject CRZ speed edits on both FMCs while the displayed target is
  owned by MCP Speed Intervention; preserve existing pending speed edits.
- Add I39: subtract extra step burn from W/STEP arrival fuel and convert the
  complete result to the selected fuel unit.
- Include all three in the standalone and both MTK modules. Source totals:
  21 catalog items, 19 Lua-delta families, 18 payloads; standalone 17 fixes.
- Correct the standalone installer's payload-count guard from 13 to 16 for
  the added fixes. Exact source/result checks and foreign-edit protection remain.
- Pass 11 package, installer and focused behavior tests, including defect-
  sensitive I30 and I37-I39 cases; all six behavior tests also pass in LuaJIT.
  Pass all 576 FMS composition cases with released MTK 0.29.4/catalog 2.0.2,
  six full-script LuaJIT loads and 72 composed-output behavior executions.
  Full-aircraft MTK installation/recovery and simulator acceptance remain open.
- Publish separate standalone and MTK source archives at the same version.
  MTK catalog qualification remains a separate step.
- Include standalone ownership and rollback guards introduced since the first
  standalone release. Older standalone installs must be removed with their
  original installer before installing 0.1.2.

## 0.1.1 — 2026-09-26

- Publish the separate schema-5 MTK source package. The standalone installer
  remained at 0.1.0.

## 0.1.0 — 2026-09-26

- Publish the first fix-only source package with 18 reviewed fix families.
- Provide 15 structural payload documents for 16 Lua-delta families.
- Record I14 as satisfied by CPDLC 1.2 and I29 as satisfied by clean .35.
- Add conditional CPDLC I06 and LevelUp W&B I33 payloads for MTK composition.
- Add the strict clean-.35 standalone installer for 14 unconditional fixes.
- Verify the 18-case composition/Lua-syntax matrix and the standalone
  check/install/verify/repeated-install/uninstall lifecycle.
