"use client";
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { api } from "./api";
import { Progress } from "./progress";
import type { RunResult } from "./types";
import { safeError } from "../../lib/api/errors";
type Phase = "idle" | "preparing" | "processing" | "loading";
interface Context {
  run: RunResult | null;
  phase: Phase;
  error: string | null;
  health: "preparing" | "ready" | "unavailable";
  busy: boolean;
  startDemo: () => Promise<void>;
  refresh: () => Promise<boolean>;
  decide: (id: string, action: "approve" | "reject") => Promise<void>;
  href: (path: string) => string;
}
export const RunContext = createContext<Context | null>(null);
export function RunProvider({ children }: { children: ReactNode }) {
  const router = useRouter(),
    pathname = usePathname(),
    urlRunId = useSearchParams().get("run_id");
  const [run, setRun] = useState<RunResult | null>(null),
    [phase, setPhase] = useState<Phase>("idle"),
    [error, setError] = useState<string | null>(null),
    [health, setHealth] = useState<Context["health"]>("preparing"),
    [busy, setBusy] = useState(false);
  const current = useRef<RunResult | null>(null),
    locked = useRef(false),
    generation = useRef(0),
    healthRequest = useRef<Promise<void> | null>(null);
  const accept = useCallback((next: RunResult) => {
    current.current = next;
    setRun(next);
    try {
      sessionStorage.setItem("reconra.current-run", next.run_id);
    } catch {
      /* Navigation context still works without storage. */
    }
  }, []);
  const warm = useCallback(async () => {
    setHealth("preparing");
    healthRequest.current ??= api.health();
    try {
      await healthRequest.current;
      setHealth("ready");
    } catch (e) {
      setHealth("unavailable");
      throw e;
    } finally {
      healthRequest.current = null;
    }
  }, []);
  useEffect(() => {
    void warm().catch((e) => setError(safeError(e)));
  }, [warm]);
  useEffect(() => {
    let id = urlRunId;
    try {
      id ??= sessionStorage.getItem("reconra.current-run");
    } catch {}
    if (!id || current.current?.run_id === id || locked.current) return;
    const token = ++generation.current;
    setPhase("loading");
    setError(null);
    setRun(null);
    current.current = null;
    void api
      .run(id)
      .then((next) => {
        if (token === generation.current) accept(next);
      })
      .catch((e) => {
        if (token === generation.current) setError(safeError(e));
      })
      .finally(() => {
        if (token === generation.current) setPhase("idle");
      });
  }, [pathname, urlRunId, accept, busy]);
  async function startDemo() {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    generation.current++;
    setError(null);
    setPhase("preparing");
    setRun(null);
    current.current = null;
    try {
      sessionStorage.removeItem("reconra.current-run");
    } catch {}
    try {
      await warm();
      setPhase("processing");

      const next = await api.demo();
      accept(next);
      router.push(`/workspace?run_id=${encodeURIComponent(next.run_id)}`);
    } catch (e) {
      setError(safeError(e));
    } finally {
      setPhase("idle");
      setBusy(false);
      locked.current = false;
    }
  }
  async function refresh() {
    if (locked.current || !current.current) return false;
    locked.current = true;
    setBusy(true);
    setError(null);
    try {
      accept(await api.run(current.current.run_id));
      return true;
    } catch (e) {
      setRun(null);
      setError(safeError(e));
      return false;
    } finally {
      setBusy(false);
      locked.current = false;
    }
  }
  async function decide(id: string, action: "approve" | "reject") {
    if (locked.current || !current.current) return;
    locked.current = true;
    setBusy(true);
    setError(null);
    const runId = current.current.run_id;
    try {
      const next = await api.decide(runId, id, action);
      accept(next);
      try {
        accept(await api.run(runId));
      } catch (e) {
        setError(`Decision recorded. ${safeError(e)}`);
      }
    } catch (e) {
      throw e;
    } finally {
      setBusy(false);
      locked.current = false;
    }
  }
  const href = (path: string) =>
    run ? `${path}?run_id=${encodeURIComponent(run.run_id)}` : path;
  return (
    <RunContext.Provider
      value={{
        run: urlRunId && run?.run_id !== urlRunId ? null : run,
        phase,
        error,
        health,
        busy,
        startDemo,
        refresh,
        decide,
        href,
      }}
    >
      {children}
    </RunContext.Provider>
  );
}
export function useRun() {
  const context = useContext(RunContext);
  if (!context) throw new Error("RunProvider is required");
  return context;
}
export function EngineNotice() {
  const { health, phase, error } = useRun();
  return (
    <div className="engine-notice">
      {(health === "preparing" || phase === "preparing") && (
        <p role="status">Preparing reconciliation engine…</p>
      )}
      {phase === "processing" && (
        <>
          <p role="status">Reconciling source evidence…</p>
          <Progress run={null} />
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
