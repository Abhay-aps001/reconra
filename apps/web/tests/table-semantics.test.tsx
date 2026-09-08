import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const tableSources = [
  "../features/exceptions/exception-list.tsx",
  "../features/imports/import-workflow.tsx",
  "../features/ledger/ledger-table.tsx",
  "../features/runs/run-history.tsx",
];

test("operational data tables identify every header as a column header", () => {
  for (const source of tableSources) {
    const content = readFileSync(new URL(source, import.meta.url), "utf8");
    for (const header of content.match(/<th\b[^>]*>/g) ?? []) {
      assert.match(header, /scope="col"/);
    }
  }
});

test("scrollable imported and saved-run tables are keyboard-reachable regions", () => {
  for (const source of [
    "../features/imports/import-workflow.tsx",
    "../features/runs/run-history.tsx",
  ]) {
    const content = readFileSync(new URL(source, import.meta.url), "utf8");
    assert.match(content, /className="table-scroll"[^>]*tabIndex=\{0\}[^>]*role="region"[^>]*aria-label=/);
  }
});
