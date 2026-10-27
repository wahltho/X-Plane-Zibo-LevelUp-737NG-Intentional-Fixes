"""Pin published companion sources; prepare only disposable FMS test inputs.

Usage: python3 tests/mtk_matrix/prepare.py <existing-evidence-directory>
Requires the downloaded Core 0.30.4 and catalog 2.0.5 in that directory.
Does not produce a release archive or modify another repository/installation.
"""

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(sys.argv[1]).resolve()
FMS = "plugins/xlua/scripts/B738.a_fms/B738.a_fms.lua"
BASELINE = Path("/Users/wahltho/dev/Zibo Mod/Original/Zibo Mod Original/B738X_XP12_4_05_35") / FMS


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


catalog_bytes = (OUTPUT / "content-package-catalog.json").read_bytes()
assert sha(catalog_bytes) == "8366ced00f1903457bdb507ed247d16e4fcc47523637c9a2992e4799773ffe99"
core = OUTPUT / "LevelUp.NavTableUpdater.Core.dll"
assert sha(core.read_bytes()) == "87963231bf1c1565aaeb06d3bd1eb08f5462023c907713b8db5546d8fa48629d"
archive = OUTPUT / "XPlane737NGMaintenanceToolkit-stable-osx-arm64-Portable.zip"
assert sha(archive.read_bytes()) == "64771a7f9a9a4b457aebdee3a086671c5e057b705f318e303a9b72e04c1a1c6d"
with zipfile.ZipFile(archive) as released:
    member, = [p for p in released.namelist() if p.endswith("/LevelUp.NavTableUpdater.Core.dll")]
    assert released.read(member) == core.read_bytes()
original = BASELINE.read_bytes()
assert sha(original) == "ff313b0e88c62845ad1c4a2b1f4bd599f57d8799e8d6707bfc10a3369fd63a8e"
(OUTPUT / "original.lua").write_bytes(original)
catalog = json.loads(catalog_bytes)
assert catalog["catalogVersion"] == "2.0.5"
artifacts = catalog["aircraftCompatibility"]["artifacts"]
groups = [p for p in catalog["packages"] if p["distribution"]["kind"] == "catalogGroup"]
modules = []; pins = []; empty = []; cache = {}


def published(member):
    pid = member["packageId"]
    if pid in cache:
        return cache[pid]
    artifact, = [a for a in artifacts if a["packageId"] == pid]
    entry, = [p for p in catalog["packages"] if p["packageId"] == pid]
    download = OUTPUT / "downloads" / pid
    download.mkdir(parents=True, exist_ok=True)
    archive_path = download / artifact["archive"]["path"]
    if not archive_path.exists():
        subprocess.run(["gh", "release", "download", artifact["releaseTag"], "--repo",
                        entry["repositoryUrl"].removeprefix("https://github.com/"),
                        "--pattern", archive_path.name, "--dir", str(download)], check=True)
    content = archive_path.read_bytes()
    assert len(content) == artifact["archive"]["size"] and sha(content) == artifact["archive"]["sha256"], pid
    with zipfile.ZipFile(archive_path) as bundle:
        files = {p: bundle.read(p) for p in bundle.namelist() if not p.endswith("/")}
    name, = [p for p in files if p == member["manifestPath"] or p.endswith("/" + member["manifestPath"])]
    assert sha(files[name]) == artifact["manifestSha256"], pid
    prefix = name[:-len(member["manifestPath"])]
    files = {p[len(prefix):]: b for p, b in files.items() if p.startswith(prefix)}
    pins.append({"packageId": pid, "artifact": artifact, "repositoryUrl": entry["repositoryUrl"]})
    cache[pid] = (files, files[member["manifestPath"]])
    return cache[pid]


for group in groups:
    product, = group["supportedProducts"]
    for member in group["members"]:
        mid = member["moduleId"]
        if mid.startswith("intentional-fixes-"):
            definition = json.loads((ROOT / "package-manifest.json").read_bytes())
            module, = [m for m in definition["modules"] if m["moduleId"] == mid]
            files = {"modules/" + mid + "/" + p["path"]: (ROOT / "src/fixes" / p["path"]).read_bytes()
                     for p in module["payloads"]}
            payload_prefix = "modules/" + mid + "/"
        else:
            files, manifest = published(member)
            if member["sourceFormat"] == "vnav":
                text = manifest.decode()
                payloads = {}
                for line in text.splitlines():
                    row = line.split("|")
                    if row[0] == "payload":
                        data = files[row[2]]
                        assert len(data) == int(row[4]) and sha(data) == row[6]
                        payloads[row[2]] = base64.b64encode(data).decode()
                operation = {"format": "vnav-manifest-v1", "manifestText": text, "payloads": payloads}
                modules.append({"product": product, "id": mid, "order": member["installationOrder"],
                                "ops": [{"operation": "vnav-manifest-v1", "payload": operation, "when": []}]})
                continue
            definition = json.loads(manifest)
            if member["sourceFormat"] == "compatibility":
                module, = [m for m in definition["modules"] if m["moduleId"] == mid]
                payload_prefix = "modules/" + mid + "/"
            else:
                module = definition
                payload_prefix = ""
        for item in module["payloads"]:
            data = files[payload_prefix + item["path"]]
            assert len(data) == item["size"] and sha(data) == item["sha256"], (mid, item["path"])
        ops = []
        for target in module["targets"]:
            if target["relativePath"] != FMS:
                continue
            assert target["operation"] != "copy-file-v1", "Unexpected complete FMS replacement"
            payload = json.loads(files[payload_prefix + target["payload"]])
            ops.append({"operation": target["operation"], "payload": payload,
                        "when": target.get("whenModulesSelected", [])})
        if ops:
            modules.append({"product": product, "id": mid, "order": member["installationOrder"], "ops": ops})
        else:
            empty.append({"product": product, "moduleId": mid, "reason": "No target on B738.a_fms.lua"})

# Exercise the real schema-5 loader too, without building a distribution ZIP.
spec = importlib.util.spec_from_file_location("mtk_fixture_package", ROOT / "tools/build_mtk_package.py")
builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
for relative, content in builder.package_files().items():
    target = OUTPUT / "candidate-package" / relative
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(content)
write_json(OUTPUT / "matrix-input.json", {"modules": modules, "emptyFmsSurfaces": empty})
write_json(OUTPUT / "input-pins.json", {
    "catalogSha256": sha(catalog_bytes), "coreSha256": sha(core.read_bytes()),
    "baselineSha256": sha(original), "publishedCompanions": pins,
    "candidateFiles": {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in
                       [ROOT / "package-manifest.json", ROOT / "standalone-manifest.json", ROOT / "z_Install.py"]
                       + sorted((ROOT / "src/fixes").glob("*.json"))},
    "limitation": "FMS source compatibility only, not full-aircraft or catalog-qualified installation proof"
})
print(f"Prepared {len(modules)} FMS module surfaces; {len(empty)} other module surfaces have no FMS target", flush=True)
