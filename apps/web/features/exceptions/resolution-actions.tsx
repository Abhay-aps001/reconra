"use client";
import { useState } from "react";
import { useRun } from "../reconciliation/run-controller";
import { ApiError, safeError } from "../../lib/api/errors";
export function ResolutionActions({ id }: { id: string }) {
  const { decide, busy, refresh } = useRun();
  const [error, setError] = useState<string | null>(null),
    [conflict, setConflict] = useState(false),
    [message, setMessage] = useState("");
  async function submit(action: "approve" | "reject") {
    setError(null);
    setMessage("");
    try {
      await decide(id, action);
      setMessage("Decision recorded. The backend run has been refreshed.");
    } catch (e) {
      setError(safeError(e));
      setConflict(e instanceof ApiError && e.status === 409);
    }
  }
  return (
    <section className="resolution-actions">
      <p>
        Approval asks the backend to reverify the stored proposal before
        applying any financial impact.
      </p>
      <div>
        <button
          className="control-button primary"
          disabled={busy || conflict}
          onClick={() => void submit("approve")}
        >
          Approve resolution
        </button>
        <button
          className="control-button"
          disabled={busy || conflict}
          onClick={() => void submit("reject")}
        >
          Reject proposal
        </button>
      </div>
      {busy && <p role="status">Submitting decision…</p>}
      {message && <p role="status">{message}</p>}
      {error && (
        <p role="alert" className="notice-error">
          {error}
        </p>
      )}
      {conflict && (
        <button
          className="control-button"
          disabled={busy}
          onClick={() =>
            void refresh().then((ok) => {
              if (ok) {
                setConflict(false);
                setError(null);
              }
            })
          }
        >
          Refresh current evidence
        </button>
      )}
    </section>
  );
}
