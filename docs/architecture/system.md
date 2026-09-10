# Reconra system architecture

Reconra separates financial truth, residual reasoning, and presentation. The reconciliation engine consumes canonical input artifacts only; it does not import synthetic-generator code, held-out truth, or scenario labels.

~~~mermaid
flowchart LR
  UI[Next.js workstation] --> API[FastAPI API]
  API --> Engine[Deterministic engine]
  Engine --> Result[Validated results and artifacts]
  Engine --> Evidence[Sanitized residual evidence]
  Evidence --> AI[Optional structured AI reasoner]
  AI --> Gate[Deterministic verifier and risk gate]
  Gate --> Result
  Result --> UI
  Result --> History[Browser-only IndexedDB snapshots]
~~~

    Next.js workstation
          |
       FastAPI API
          |
    deterministic engine --> validated result and artifacts --> browser UI / IndexedDB snapshots
          |
    sanitized residual evidence --> optional structured AI reasoner
                                      |
                            deterministic verifier and risk gate
                                      |
                            validated result and artifacts

The API owns live runs and returns a validated RunResult. The browser records up to ten public snapshots as a convenience only. A snapshot is visibly saved-only: it cannot approve/reject an exception or download a live artifact.

The optional AI reasoner receives residual evidence packets, returns structured proposals, and has no arithmetic or mutation authority. A proposal can affect a reconciliation only through deterministic verification, risk gating, idempotency validation, and backend persistence.

Razorpay data, when enabled, enters through a server-side Test Mode read-only retrieval boundary. Import files are inspected and reconciled by the backend; browser history does not retain raw uploads.
