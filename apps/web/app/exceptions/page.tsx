"use client";
import { useRun } from "../../features/reconciliation/run-controller";
import { RunScreen } from "../../features/reconciliation/run-screen";
import { TieOutRail } from "../../components/tie-out/tie-out-rail";
import { ExceptionList } from "../../features/exceptions/exception-list";
export default function Exceptions() {
  const { run } = useRun();
  return (
    <RunScreen
      title="Exception workbench"
      description="Evidence first. Verify every proposal before financial impact."
    >
      {run && (
        <>
          <TieOutRail value={run.tie_out_summary} />
          <ExceptionList />
        </>
      )}
    </RunScreen>
  );
}
