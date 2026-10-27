using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using LevelUp.NavTableUpdater.Core.Aircraft;
using LevelUp.NavTableUpdater.Core.Content;
using LevelUp.NavTableUpdater.Core.Content.PatchHandlers;
using LevelUp.NavTableUpdater.Core.State;

// Released handlers, unchanged sources/order; no aircraft or catalog mutation.
var root = Path.GetFullPath(args.Single());
string Hash(byte[] b) => Convert.ToHexString(SHA256.HashData(b)).ToLowerInvariant();
void Require(bool ok, string message) { if (!ok) throw new Exception(message); }
Require(Hash(File.ReadAllBytes(typeof(ContentPackageCatalog).Assembly.Location)) ==
    "87963231bf1c1565aaeb06d3bd1eb08f5462023c907713b8db5546d8fa48629d", "Unmodified released Core required");
Require(typeof(ContentPackageCatalog).Assembly.GetName().Version == new Version(0,30,4,0), "Core version");
var catalog = ContentPackageCatalog.Parse(File.ReadAllText(Path.Combine(root,"content-package-catalog.json")),new Version(0,30,4));
var package = CompatibilityPackageLoader.LoadDirectory(Path.Combine(root,"candidate-package"));
Require(package.Manifest.SchemaVersion == 5, "Candidate parser schema");
using var input = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(root,"matrix-input.json")));
var original = File.ReadAllBytes(Path.Combine(root,"original.lua"));
var lf = Encoding.UTF8.GetString(original).Replace("\r\n","\n");
var registry = ContentPatchHandlerRegistry.CreateBuiltIn();
var results = new List<object>(); var failures = 0;
var output = Path.Combine(root,"composed"); Directory.CreateDirectory(output);
foreach(var product in new[]{"zibo-737ng","levelup-737ng"}) {
    var modules = input.RootElement.GetProperty("modules").EnumerateArray()
        .Where(m => m.GetProperty("product").GetString() == product)
        .OrderBy(m => m.GetProperty("order").GetInt32()).ToArray();
    var optional = modules.Where(m => !m.GetProperty("id").GetString()!.StartsWith("intentional-fixes-")).ToArray();
    foreach(var style in new[]{"original","lf","crlf-bom"}) {
        var baseline = style == "original" ? original : Encoding.UTF8.GetBytes(style == "lf" ? lf : "\ufeff"+lf.Replace("\n","\r\n"));
        for(int mask=0;mask<(1<<optional.Length);mask++) {
            var selected = optional.Where((m,i) => (mask & (1<<i)) != 0)
                .Select(m => m.GetProperty("id").GetString()!).ToHashSet(StringComparer.Ordinal);
            selected.Add(product == "zibo-737ng" ? "intentional-fixes-zibo" : "intentional-fixes-levelup");
            var id = product+"-"+style+"-"+mask;
            byte[] Compose(byte[] source) {
                var current = source;
                foreach(var module in modules.Where(m => selected.Contains(m.GetProperty("id").GetString()!)))
                foreach(var op in module.GetProperty("ops").EnumerateArray()) {
                    if(!op.GetProperty("when").EnumerateArray().All(m => selected.Contains(m.GetString()!))) continue;
                    current = registry.GetRequired(op.GetProperty("operation").GetString()!).Apply(current,op.GetProperty("payload"));
                }
                return current;
            }
            try {
                var composed = Compose(baseline);
                // MTK 0.30.4 rebuilds managed shared files from the verified
                // original backup. It does not rerun earlier module payloads
                // over blocks intentionally refined by a later module (I33).
                Require(composed.SequenceEqual(Compose(baseline)),"Repeated clean-baseline composition differs");
                if(mask == (1<<optional.Length)-1) {
                    var reapplied = composed;
                    foreach(var module in modules.Where(m => m.GetProperty("id").GetString()!.StartsWith("intentional-fixes-")))
                    foreach(var op in module.GetProperty("ops").EnumerateArray()) {
                        if(!op.GetProperty("when").EnumerateArray().All(m => selected.Contains(m.GetString()!))) continue;
                        reapplied = registry.GetRequired(op.GetProperty("operation").GetString()!).Apply(reapplied,op.GetProperty("payload"));
                    }
                    Require(composed.SequenceEqual(reapplied),"Intentional Fixes self-reapplication differs");
                    if(product == "levelup-737ng") {
                        string? rejection = null;
                        try { Compose(composed); } catch(InvalidOperationException ex) { rejection = ex.Message; }
                        Require(rejection?.Contains("LevelUp W&B FMS ACF empty-weight binding") == true,
                            "Unsupported whole-pipeline-on-output negative control changed");
                    }
                }
                var text = Encoding.UTF8.GetString(composed);
                Require(text.StartsWith("\ufeff",StringComparison.Ordinal) == (style == "crlf-bom"),"BOM preservation");
                Require(style == "lf" ? !text.Contains("\r") : !text.Replace("\r\n","").Contains('\n'),"Line-ending preservation");
                foreach(var marker in new[]{"passed waypoint restriction cannot become", "displayed CRZ /MCP target belongs", "extra step burn reduces arrival fuel", "BEGIN CUSTOM I40 VI source publication lifetime"})
                    Require(text.Contains(marker),"Missing new payload: "+marker);
                var path = Path.Combine(output,id+".lua"); File.WriteAllBytes(path,composed);
                var start = new ProcessStartInfo("luac") { RedirectStandardOutput=true,RedirectStandardError=true };
                start.ArgumentList.Add("-p"); start.ArgumentList.Add(path);
                using var syntax = Process.Start(start)!;
                var error = syntax.StandardError.ReadToEnd(); syntax.WaitForExit();
                Require(syntax.ExitCode == 0,"Lua syntax: "+error);
                results.Add(new { id,status="PASS",selected=selected.Order().ToArray(),sha256=Hash(composed) });
                // Keep only all-selected representatives for component execution.
                if(mask != (1<<optional.Length)-1) File.Delete(path);
            } catch(Exception ex) {
                failures++; results.Add(new { id,status="FAIL",selected=selected.Order().ToArray(),error=ex.Message });
                Console.WriteLine("FAIL "+id+": "+ex.Message);
            }
        }
        Console.WriteLine(product+" / "+style+": "+(1<<optional.Length)+" selections completed");
    }
}
// The unreleased source must NOT pass current release-provenance admission.
var aircraft = Path.Combine(root,"qualification-negative-control"); Directory.CreateDirectory(aircraft);
var acf = Path.Combine(aircraft,"b738.acf"); File.WriteAllText(acf,"fixture only\n");
var variant = new AircraftVariantViewAnalysis("zibo-737-800","Zibo","Zibo",acf,
    Path.ChangeExtension(acf,null)+"_prefs.txt","fixture","fixture","4.05.35","4.05.35",
    null,null,null,null,0,0,null,null,null,null,"fixture","fixture","fixture","fixture");
var planner = new CompatibilityPackagePlanBuilder(new ToolStateStore(Path.Combine(root,"state"),Path.Combine(root,"backups")),catalogProvider:()=>catalog);
var plan = await planner.BuildAsync(ContentPatchAction.Install,variant,package,["intentional-fixes-zibo"]);
Require(!plan.IsSafe && plan.StatusMessage.Contains("catalog group"),"Unreleased source unexpectedly admitted as a catalog-qualified release");
File.WriteAllText(Path.Combine(root,"matrix-results.json"),JsonSerializer.Serialize(new {
    core="0.30.4",catalog="2.0.5",results,failures,
    provenanceNegativeControl=plan.StatusMessage,
    repeatContract="Recompose selected pipeline from the frozen original, as managed MTK does; all-selected IF self-reapplication also byte-identical. Direct whole-pipeline reapplication rejects I33-refined W&B and is not the MTK managed-repeat contract.",
    limitation="Actual released FMS patch handlers; not full-aircraft install/rollback or catalog qualification."
},new JsonSerializerOptions{WriteIndented=true})+"\n");
Console.WriteLine($"Matrix complete: {results.Count-failures} PASS / {failures} FAIL; qualification negative control PASS");
return failures == 0 ? 0 : 1;
