"use client";
import { useRun } from "../../features/reconciliation/run-controller";
import { RunScreen } from "../../features/reconciliation/run-screen";
import { Progress } from "../../features/reconciliation/progress";
import { TieOutRail } from "../../components/tie-out/tie-out-rail";
import { RunOverview } from "../../features/reconciliation/run-overview";
export default function Workspace() {
  const { run, phase } = useRun();
  return (
    <>
      <RunScreen
        title={
          run?.status === "COMPLETED"
            ? "Reconciliation complete"
            : "Reconciliation workspace"
        }
        description="A source-backed view of every explained and unresolved rupee."
      >
        {run && (
          <>
            <TieOutRail value={run.tie_out_summary} />
            <RunOverview run={run} />
            <Progress run={run} />
          </>
        )}
      </RunScreen>
      {phase === "processing" && <Progress run={null} />}
    </>
  );
}
