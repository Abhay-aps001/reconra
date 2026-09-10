# Security and data boundaries

## Credentials

Secrets are read only at server-side integration boundaries. They are not stored in frontend code, browser snapshots, prompts, committed files, or ordinary CI. .env files are ignored; .env.example lists variable names only.

## Financial authority

The backend owns live reconciliation state. The frontend validates and presents public run results but does not calculate financial truth, mutate ledger values, or turn formatted currency into money values.

## AI boundary

AI is restricted to residual ambiguity and structured proposals. It has no authority to calculate fees, GST, taxes, settlement totals, or accounting values, and cannot directly mutate reconciliation state. Raw bank statements are not sent to the optional provider; residual evidence is sanitized before that boundary.

## Imports and storage

Supported imports are CSV, XLSX, and controlled text/table PDF. Scanned-PDF OCR is unsupported. Raw uploads are not retained in browser run history. Recent run snapshots are public, parsed RunResult data held in browser IndexedDB only, with a maximum of ten snapshots.

## Razorpay

Razorpay is Test Mode only and read-only. There are no production controls or payment, capture, refund, payout, or settlement mutation endpoints in the product.

## Limitations

Reconra has no authentication or durable server database in this repository state. The API run store is transient. A saved benchmark result is explicitly non-live evidence and never a current reconciliation result.
