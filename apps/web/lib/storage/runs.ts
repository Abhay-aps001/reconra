import { parseRun, type RunResult } from "../../features/reconciliation/types";

const DATABASE = "reconra-runs";
const STORE = "snapshots";
const MAX_SNAPSHOTS = 10;

export interface RunSnapshot {
  schema_version: 1;
  saved_at: string;
  run: RunResult;
}

export interface RunSnapshotSummary {
  run_id: string;
  saved_at: string;
  status: RunResult["status"];
  total_bank_credit_paise: number;
  explained_bank_credit_paise: number;
  unexplained_residual_paise: number;
  exception_count: number;
}

export function sanitizeRunSnapshot(value: unknown, savedAt = new Date().toISOString()): RunSnapshot {
  if (!Number.isFinite(Date.parse(savedAt))) throw new Error("Invalid snapshot date");
  return { schema_version: 1, saved_at: savedAt, run: parseRun(value) };
}

function parseSnapshot(value: unknown): RunSnapshot | undefined {
  try {
    const raw = value as Record<string, unknown>;
    if (!raw || raw.schema_version !== 1 || typeof raw.saved_at !== "string") return undefined;
    return sanitizeRunSnapshot(raw.run, raw.saved_at);
  } catch {
    return undefined;
  }
}

export function pruneSnapshots(values: unknown[]): RunSnapshot[] {
  const unique = new Map<string, RunSnapshot>();
  for (const value of values) {
    const snapshot = parseSnapshot(value);
    if (!snapshot) continue;
    const existing = unique.get(snapshot.run.run_id);
    if (!existing || existing.saved_at <= snapshot.saved_at) unique.set(snapshot.run.run_id, snapshot);
  }
  return [...unique.values()]
    .sort((a, b) => b.saved_at.localeCompare(a.saved_at))
    .slice(0, MAX_SNAPSHOTS);
}

export function summarizeRunSnapshot(snapshot: RunSnapshot): RunSnapshotSummary {
  const { run } = snapshot;
  return {
    run_id: run.run_id,
    saved_at: snapshot.saved_at,
    status: run.status,
    total_bank_credit_paise: run.tie_out_summary.total_bank_credit_paise,
    explained_bank_credit_paise: run.tie_out_summary.explained_bank_credit_paise,
    unexplained_residual_paise: run.tie_out_summary.unexplained_residual_paise,
    exception_count: run.exceptions.length,
  };
}

function database(): Promise<IDBDatabase> | undefined {
  if (typeof indexedDB === "undefined") return undefined;
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE)) request.result.createObjectStore(STORE, { keyPath: "run.run_id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function allSnapshots(): Promise<RunSnapshot[]> {
  const db = database();
  if (!db) return [];
  try {
    const connection = await db;
    const values = await new Promise<unknown[]>((resolve, reject) => {
      const request = connection.transaction(STORE, "readonly").objectStore(STORE).getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    connection.close();
    return pruneSnapshots(values);
  } catch {
    return [];
  }
}

async function replaceAll(snapshots: RunSnapshot[]): Promise<void> {
  const db = database();
  if (!db) return;
  try {
    const connection = await db;
    await new Promise<void>((resolve, reject) => {
      const transaction = connection.transaction(STORE, "readwrite");
      const store = transaction.objectStore(STORE);
      store.clear();
      snapshots.forEach((snapshot) => store.put(snapshot));
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
    connection.close();
  } catch {
    // Browser storage is an optional convenience, never a reconciliation failure.
  }
}

export async function saveRunSnapshot(snapshot: RunSnapshot): Promise<void> {
  const saved = sanitizeRunSnapshot(snapshot.run, snapshot.saved_at);
  await replaceAll(pruneSnapshots([...(await allSnapshots()), saved]));
}

export async function listRunSnapshots(): Promise<RunSnapshotSummary[]> {
  return (await allSnapshots()).map(summarizeRunSnapshot);
}

export async function getRunSnapshot(runId: string): Promise<RunSnapshot | undefined> {
  return (await allSnapshots()).find((snapshot) => snapshot.run.run_id === runId);
}

export async function deleteRunSnapshot(runId: string): Promise<void> {
  await replaceAll((await allSnapshots()).filter((snapshot) => snapshot.run.run_id !== runId));
}
