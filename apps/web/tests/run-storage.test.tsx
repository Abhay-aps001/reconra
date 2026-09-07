import assert from "node:assert/strict";
import test from "node:test";
import { runFixture } from "../../../tests/e2e/fixtures/run";
import {
  sanitizeRunSnapshot,
  summarizeRunSnapshot,
  pruneSnapshots,
  deleteRunSnapshot,
  getRunSnapshot,
  listRunSnapshots,
  type RunSnapshot,
} from "../lib/storage/runs";

function snapshot(runId: string, savedAt: string): RunSnapshot {
  const base = runFixture();
  return sanitizeRunSnapshot(
    {
      ...base,
      run_id: runId,
      audit_events: base.audit_events.map((event) => ({ ...event, run_id: runId })),
    },
    savedAt,
  );
}

test("sanitizes only valid public run data into schema version 1 snapshots", () => {
  const saved = snapshot("run_saved", "2026-09-07T10:00:00.000Z");
  assert.equal(saved.schema_version, 1);
  assert.equal(saved.run.run_id, "run_saved");
  assert.deepEqual(summarizeRunSnapshot(saved).run_id, "run_saved");
  assert.throws(() => sanitizeRunSnapshot({ ...runFixture(), tie_out_summary: { total_bank_credit_paise: 1, explained_bank_credit_paise: 0, unexplained_residual_paise: 0 } }, "2026-09-07T10:00:00.000Z"));
});

test("keeps newest unique snapshots first and prunes the eleventh distinct run", () => {
  const snapshots = Array.from({ length: 11 }, (_, index) =>
    snapshot(`run_${index}`, `2026-09-${String(index + 1).padStart(2, "0")}T00:00:00.000Z`),
  );
  const result = pruneSnapshots(snapshots);
  assert.equal(result.length, 10);
  assert.equal(result[0].run.run_id, "run_10");
  assert.equal(result.at(-1)?.run.run_id, "run_1");
  const updated = pruneSnapshots([...result, snapshot("run_5", "2026-10-01T00:00:00.000Z")]);
  assert.equal(updated.filter((entry) => entry.run.run_id === "run_5").length, 1);
  assert.equal(updated[0].run.run_id, "run_5");
  const sameMoment = pruneSnapshots([snapshot("run_same", "2026-10-01T00:00:00.000Z"), snapshot("run_same", "2026-10-01T00:00:00.000Z")]);
  assert.equal(sameMoment.length, 1);
});

test("skips corrupt and unsupported snapshot records", () => {
  const valid = snapshot("run_valid", "2026-09-07T10:00:00.000Z");
  const result = pruneSnapshots([valid, { ...valid, schema_version: 2 }, { schema_version: 1 }] as unknown[]);
  assert.deepEqual(result.map((entry) => entry.run.run_id), ["run_valid"]);
});

test("storage-unavailable reads, missing IDs, and deletes are non-fatal", async () => {
  assert.deepEqual(await listRunSnapshots(), []);
  assert.equal(await getRunSnapshot("missing"), undefined);
  await deleteRunSnapshot("missing");
});
