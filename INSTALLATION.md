# Standalone installation — clean .35 only

> This installer is unofficial and is not supported by Zibo, LevelUp or
> Laminar Research. Support is provided only through the
> [wahltho Discord server](https://discord.gg/ySS88PMuyC). Do not request
> support through official product channels.

The standalone installer is intentionally narrower than the Maintenance
Toolkit package. It accepts only the untouched original Zibo 4.05.35
`B738.a_fms.lua`, which is currently byte-identical in the Zibo original and
the LevelUp repository:

`ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e`

Do not use it on an aircraft carrying CPDLC, LevelUp W&B, VNAV or any other Lua
patch. Use the Maintenance Toolkit for composed installations.

Run from this package directory, with X-Plane stopped:

```text
python3 z_Install.py check --aircraft-root "/path/to/B737-800X"
python3 z_Install.py install --aircraft-root "/path/to/B737-800X"
python3 z_Install.py verify --aircraft-root "/path/to/B737-800X"
python3 z_Install.py uninstall --aircraft-root "/path/to/B737-800X"
```

`check` performs the full composition and result-hash validation without
writing aircraft files. `install` saves the exact original Lua under
`.zibo-intentional-fixes-clean35/`, writes the complete result atomically, and
records its state. A repeated install verifies and leaves the file unchanged.
`uninstall` refuses a modified installed Lua and restores the exact saved
original before removing its private state directory.

The standalone build contains 14 fixes through 13 unconditional payloads:
I01-I05, I07-I09, I16, I24, I27, I30, I34 and I35. I29 is already satisfied by
clean .35. CPDLC-dependent I06/I14 and W&B-dependent I33 are intentionally not
included.
