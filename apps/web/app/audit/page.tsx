"use client";
import { useRun } from "../../features/reconciliation/run-controller";
import { RunScreen } from "../../features/reconciliation/run-screen";
import { TieOutRail } from "../../components/tie-out/tie-out-rail";
import { AuditTimeline } from "../../features/audit/audit-timeline";
export default function Audit() {
  const { run } = useRun();
  return (
    <RunScreen
      title="Audit trail"
      description="The recorded decision lifecycle, in backend event order."
    >
      {run && (
        <>
          <TieOutRail value={run.tie_out_summary} />
          <AuditTimeline key={run.run_id} events={run.audit_events} />
        </>
      )}
    </RunScreen>
  );
}
