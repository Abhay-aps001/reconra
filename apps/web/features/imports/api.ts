import { requestForm, requestJson } from "../../lib/api/client";
import { parseRun, type RunResult } from "../reconciliation/types";
import { parseInspection, type ImportInspection } from "./types";

export const importApi = {
  async inspect(files: File[]): Promise<ImportInspection> {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    return parseInspection(await requestForm("/import/inspect", form));
  },
  validate: (id: string, mappings: Record<string, Record<string, string>>) =>
    requestJson(`/import/${encodeURIComponent(id)}/validate`, { mappings }),
  reconcile: async (id: string): Promise<RunResult> => parseRun(await requestJson(`/import/${encodeURIComponent(id)}/reconcile`)),
};
