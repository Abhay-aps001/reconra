import assert from "node:assert/strict";
import test from "node:test";
import { parseInspection, supportedImportFile } from "../features/imports/types";

test("accepts only declared import formats and parses backend inspection data", () => {
  assert.equal(supportedImportFile({ name: "bank.csv" } as File), true);
  assert.equal(supportedImportFile({ name: "settlement.xlsx" } as File), true);
  assert.equal(supportedImportFile({ name: "table.pdf" } as File), true);
  assert.equal(supportedImportFile({ name: "scan.png" } as File), false);
  const inspection = parseInspection({
    import_id: "import_123",
    warnings: [],
    files: [{ filename: "bank.csv", source_type: "csv", columns: ["Txn Date"], row_count: 1, sample_rows: [{ "Txn Date": "2026-01-01" }], candidate_role: "bank_transactions", suggestions: [{ source_column: "Txn Date", target_field: "transaction_date", confidence: 1, reason: "exact_alias" }] }],
  });
  assert.equal(inspection.files[0].suggestions[0].target_field, "transaction_date");
});
