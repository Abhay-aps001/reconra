import { ApiError } from "../../lib/api/errors";

export interface ImportSuggestion { source_column: string; target_field: string; confidence: number; reason: string; }
export interface InspectedFile { filename: string; source_type: string; columns: string[]; row_count: number; sample_rows: Record<string, string>[]; candidate_role: string; suggestions: ImportSuggestion[]; }
export interface ImportInspection { import_id: string; files: InspectedFile[]; warnings: string[]; }

function invalid(): never { throw new ApiError("INVALID_RESPONSE", "The import inspection response was invalid. Please select the files again."); }
function record(value: unknown): Record<string, unknown> { if (!value || typeof value !== "object" || Array.isArray(value)) return invalid(); return value as Record<string, unknown>; }
function text(value: unknown): string { return typeof value === "string" ? value : invalid(); }

export function supportedImportFile(file: File): boolean {
  return [".csv", ".xlsx", ".pdf"].some((extension) => file.name.toLowerCase().endsWith(extension));
}

export function parseInspection(value: unknown): ImportInspection {
  const raw = record(value);
  if (!Array.isArray(raw.files) || !Array.isArray(raw.warnings)) return invalid();
  return {
    import_id: text(raw.import_id),
    warnings: raw.warnings.map(text),
    files: raw.files.map((file) => {
      const item = record(file);
      if (!Array.isArray(item.columns) || !Array.isArray(item.sample_rows) || !Array.isArray(item.suggestions) || typeof item.row_count !== "number") return invalid();
      return {
        filename: text(item.filename), source_type: text(item.source_type), columns: item.columns.map(text), row_count: item.row_count,
        sample_rows: item.sample_rows.map((row) => Object.fromEntries(Object.entries(record(row)).map(([key, value]) => [key, text(value)]))),
        candidate_role: text(item.candidate_role),
        suggestions: item.suggestions.map((suggestion) => { const s = record(suggestion); if (typeof s.confidence !== "number") return invalid(); return { source_column: text(s.source_column), target_field: text(s.target_field), confidence: s.confidence, reason: text(s.reason) }; }),
      };
    }),
  };
}
