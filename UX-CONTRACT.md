# Reconra UX contract

## Run lifecycle

`RunProvider` owns the current authoritative run. Any accepted run has passed the public response parser and exact tie-out validation before it can be displayed or saved. The provider records a sanitized browser snapshot asynchronously; storage failure never blocks a completed reconciliation.

## Saved snapshots

The Runs page keeps at most ten schema-version-1 public snapshots in IndexedDB. They are newest first. Opening a snapshot first refreshes its backend run. If unavailable, the interface labels the result `SAVED RUN SNAPSHOT`; it remains readable but cannot approve, reject, or export a backend artifact. Deletion permanently removes only the local browser snapshot and takes effect immediately.

## Imports and sync

Imports progress in order: inspect, confirm mappings, validate, reconcile. Native file input accepts CSV, XLSX, and backend-supported text/table PDFs only; the UI states that scanned-PDF OCR is unsupported. Razorpay only exposes a server-configured, read-only Test Mode sync. Neither route renders or stores credentials.

## Async feedback and accessibility

Submit controls disable while their request is in flight. Typed backend errors are rendered as plain status text, never raw response bodies. Local tables scroll inside their panels; controls use native labels and visible keyboard focus.
