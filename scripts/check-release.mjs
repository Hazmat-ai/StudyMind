import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
const root = new URL("../", import.meta.url);
const expected = JSON.parse(
  readFileSync(new URL("../deploy/release.example.json", import.meta.url)),
);
let release;
try {
  release = JSON.parse(
    readFileSync(new URL("../deploy/release.json", import.meta.url)),
  );
} catch {
  throw new Error(
    "Create deploy/release.json with observed approval evidence; see docs/RELEASE.md.",
  );
}
const dirty=execFileSync('git',['status','--porcelain'],{cwd:root,encoding:'utf8'}).trim();
if(dirty)throw new Error('Commit reviewed source changes before checking release evidence.');
const commit = execFileSync("git", ["rev-parse", "HEAD"], {
  cwd: root,
  encoding: "utf8",
}).trim();
if (release.commit !== commit)
  throw new Error("Approval must name the exact current release commit.");
for (const name of Object.keys(expected.gates)) {
  const gate = release.gates?.[name];
  if (
    gate?.approved !== true ||
    !gate.reviewer?.trim() ||
    !gate.evidence?.trim() ||
    !/^\d{4}-\d{2}-\d{2}$/.test(gate.date) ||
    !Number.isFinite(Date.parse(gate.date)) ||
    Date.parse(gate.date) > Date.now()
  )
    throw new Error(`Missing review/evidence: ${name}`);
}
console.log(
  `Release evidence present for ${commit}. This validates the record, not the truth of its approvals.`,
);
