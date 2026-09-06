"use client";
import { useRun } from "../../features/reconciliation/run-controller";
import { RunScreen } from "../../features/reconciliation/run-screen";
import { TieOutRail } from "../../components/tie-out/tie-out-rail";
import { LedgerTable } from "../../features/ledger/ledger-table";
export default function Ledger() {
  const { run } = useRun();
  return (
    <RunScreen
      title="Ledger explorer"
      description="Inspect the engine's recorded source-to-candidate matches."
    >
      {run && (
        <>
          <TieOutRail value={run.tie_out_summary} />
          <LedgerTable />
        </>
      )}
    </RunScreen>
  );
}
