"""Run the existing component oracles on all-selected released-handler outputs.

Usage: python3 tests/mtk_matrix/verify_outputs.py <evidence-directory> <luajit>
No new interpretation of the aircraft logic; fixtures remain offline.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(sys.argv[1]).resolve()
JIT = Path(sys.argv[2]).resolve()
pins = json.loads((OUTPUT / "input-pins.json").read_bytes())
matrix = json.loads((OUTPUT / "matrix-results.json").read_bytes())
assert not matrix["failures"], "Do not claim behavioral compatibility for a red composition matrix"
results = []
fixtures = sorted((OUTPUT / "composed").glob("*.lua"))
assert len(fixtures) == 6, "Two products times three line formats required"
for fixture in fixtures:
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == next(
        r["sha256"] for r in matrix["results"] if r["id"] == fixture.stem)
    # Parse/load only; never run the complete aircraft script without X-Plane.
    parse = subprocess.run([str(JIT), "-e", "assert(loadfile(" + json.dumps(str(fixture)) + "))"],
                           capture_output=True, text=True)
    assert parse.returncode == 0, parse.stdout + parse.stderr
    for runtime in ("lua54", "luajit"):
        environment = dict(os.environ, INTENTIONAL_COMPOSED_LUA=str(fixture))
        if runtime == "luajit":
            environment["PATH"] = str(JIT.parent) + os.pathsep + environment["PATH"]
        # Deterministically keep the host Lua 5.4 pass separate from LuaJIT.
        else:
            environment["PATH"] = os.pathsep.join(p for p in environment["PATH"].split(os.pathsep)
                                                   if not (Path(p) / "luajit").is_file())
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "*payloads.py", "-v"]
        run = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True)
        (OUTPUT / (fixture.stem + "-" + runtime + ".log")).write_text(run.stdout + run.stderr)
        results.append({"fixture": fixture.stem, "runtime": runtime, "exitCode": run.returncode})
        print(f"{fixture.stem} / {runtime}: {'PASS' if run.returncode == 0 else 'FAIL'}", flush=True)
        assert run.returncode == 0, run.stdout + run.stderr
for relative, expected in pins["candidateFiles"].items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative + " drifted"
test_pins = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((ROOT / "tests").rglob("*")) if p.suffix in (".py", ".cs", ".csproj")}
(OUTPUT / "behavior-results.json").write_text(json.dumps({
    "results": results, "methodsPerRun": 6, "fullScriptLuaJitLoads": len(fixtures),
    "productionInputPinsUnchanged": True, "testPins": test_pins,
    "limitation": "Stubbed component execution, not a simulator or full-aircraft integration replay"
}, indent=2) + "\n")
