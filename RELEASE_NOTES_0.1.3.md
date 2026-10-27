# Intentional Fixes 0.1.3

This release repairs I02 course decoding and adds I40.

I02 previously treated some magnetic course values as whole degrees instead
of tenths. The repair uses the declared format: `0140` is 14 degrees magnetic;
`036T` is 36 degrees true. It preserves the original token and converts at the
appropriate start point. Published HOLD time values such as `T010` stay intact.

I40 keeps a VI's prescribed heading separate from calculated track and later
plugin geometry feedback. It also corrects ground LNAV arming for the first
prescribed V-heading within 5 degrees of the actual departure runway direction,
with magnetic and true values compared in the same reference.

Both installation paths use these changes. Standalone accepts only the untouched
original .35 FMS Lua and includes 18 fix families. MTK applies earlier functional
modules first, Intentional Fixes next and Lua Timer afterwards. Conditional CPDLC
and LevelUp W&B corrections retain their existing selection rules. Updating or
removing an installation remains the responsibility of its existing installer;
see [installation instructions](INSTALLATION.md).

No pages, settings or features are added. The original `zibomod.xpl` is unchanged.
This repository distributes patch definitions, not a complete aircraft Lua file.

## Limits

These changes do not establish that the reported LGSK departure problem is
fully resolved. The component checks are not a flight replay. Native non-VI
TRUE/HOLD coherence and native behavior without valid intercept geometry remain
outside the bounded Lua repair. See [the test report](IMPLEMENTATION_0.1.3.md).
The final suite passes 23 methods under each of Lua 5.4 and LuaJIT. All 576
FMS combinations pass with released MTK 0.30.4/catalog 2.0.5, together with
six full-script LuaJIT loads and 204 component-method executions on combined
outputs. MTK catalog qualification and full-aircraft installation/recovery
remain separate.

This is my unofficial patch. It is not affiliated with, endorsed by or supported
by Zibo, LevelUp or Laminar Research. Reports and discussion belong on the
[wahltho Discord server](https://discord.gg/ySS88PMuyC), not the official aircraft
support channels.
