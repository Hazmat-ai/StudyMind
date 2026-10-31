// Audit all packages; one narrowly scoped tooling advisory is documented in SECURITY.md.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
const result = spawnSync("npm", ["audit", "--json"], {
  cwd: new URL("../frontend", import.meta.url),
  encoding: "utf8",
  maxBuffer: 10 * 1024 * 1024,
});
let report;
try {
  report = JSON.parse(result.stdout);
} catch {
  throw new Error("npm audit did not return a valid report");
}
if (report.error || !report.vulnerabilities)
  throw new Error("npm audit could not finish");
const lock = JSON.parse(
  readFileSync(new URL("../frontend/package-lock.json", import.meta.url)),
);
const allowed = "https://github.com/advisories/GHSA-g3hv-75wg-m249";
const failures = [],
  exceptions = new Set();
for (const vulnerability of Object.values(report.vulnerabilities)) {
  for (const advisory of vulnerability.via.filter(
    (v) => typeof v === "object",
  )) {
    const onlyTooling =
      vulnerability.nodes.length > 0 &&
      vulnerability.nodes.every((path) => lock.packages[path]?.dev === true);
    if (
      advisory.url === allowed &&
      onlyTooling &&
      advisory.severity === "moderate" &&
      Date.now() < Date.parse("2026-12-01T00:00:00Z")
    )
      exceptions.add(advisory.url);
    else
      failures.push(
        `${vulnerability.name}: ${advisory.url} (${advisory.severity})`,
      );
  }
}
for (const exception of exceptions)
  console.log(
    `REVIEW REQUIRED: development tooling exception until 2026-11-30: ${exception}`,
  );
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(
  `Audit completed; ${exceptions.size} documented tooling advisory; no other advisories.`,
);
