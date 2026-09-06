import { ApiError } from "../../lib/api/errors";
export interface LedgerRow {
  record_type: string;
  source_id: string;
  candidate_id: string;
  financial_impact_paise: number;
  evidence: string;
}
export function parseLedger(text: string): LedgerRow[] {
  const rows: string[][] = [];
  let row: string[] = [],
    field = "",
    quoted = false,
    closed = false;
  const fail = () => {
    throw new ApiError(
      "INVALID_ARTIFACT",
      "The ledger artifact is invalid. Please refresh the run.",
    );
  };
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          quoted = false;
          closed = true;
        }
      } else field += c;
    } else if (c === '"') {
      if (field || closed) fail();
      quoted = true;
    } else if (c === ",") {
      row.push(field);
      field = "";
      closed = false;
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      closed = false;
    } else {
      if (closed) fail();
      field += c;
    }
  }
  if (quoted) fail();
  if (field || row.length) {
    row.push(field);
    rows.push(row);
  }
  const header = rows.shift();
  const keys = [
    "record_type",
    "source_id",
    "candidate_id",
    "financial_impact_paise",
    "financial_impact_display",
    "evidence",
  ];
  if (
    !header ||
    header.length !== keys.length ||
    keys.some((k) => !header.includes(k))
  )
    fail();
  return rows
    .filter((r) => r.some(Boolean))
    .map((r) => {
      if (r.length !== header!.length) fail();
      const v = Object.fromEntries(header!.map((k, i) => [k, r[i]]));
      if (
        !/^-?\d+$/.test(v.financial_impact_paise) ||
        !Number.isSafeInteger(Number(v.financial_impact_paise)) ||
        !["payment", "settlement_bank"].includes(v.record_type) ||
        !v.source_id ||
        !v.candidate_id
      )
        fail();
      return {
        record_type: v.record_type,
        source_id: v.source_id,
        candidate_id: v.candidate_id,
        financial_impact_paise: Number(v.financial_impact_paise),
        evidence: v.evidence,
      };
    });
}
