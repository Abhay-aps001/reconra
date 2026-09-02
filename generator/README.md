# Reconra synthetic datasets

The generator produces deterministic Razorpay-style reconciliation inputs for Nivara, a fictional Indian D2C home and lifestyle merchant.

## Data contract

Each dataset has four raw finance views:

- `orders` — merchant ledger/order records;
- `payments` — captured payment records;
- `reconciliation_rows` — Razorpay combined settlement reconciliation rows;
- `bank_transactions` — bank-statement settlement evidence.

Financial values are integer paise only. Generated reconciliation rows use only the supported types `payment`, `refund`, `transfer`, and `adjustment`. Card payments use `method: "card"` with card metadata; `credit_card` and `debit_card` are not method values.

Ground truth is evaluator-only. It is written to `ground_truth.json`, never placed in a raw input collection, and never included in the raw-content SHA-256 `input_hash`. `engine/reconra` must never import `generator` or truth logic.

## Fixed roles and seeds

| Role | Seed | Purpose |
| --- | ---: | --- |
| `clean` | 1101 | 64 clean reconciliation rows for development. |
| `messy-dev` | 2202 | Broad 20-class development break coverage. |
| `demo` | 3303 | 245 meaningful lines with clean and deliberate difficult cases. |
| `heldout` | 4404 | Broad frozen evaluation data; do not tune against it after evaluation. |
| `stress` | 5505 | On-demand 10,000-row deterministic throughput fixture. |

The messy taxonomy uses canonical `BreakClass` values:

`ROUNDING_VARIANCE`, `AMOUNT_MISMATCH`, `FEE_VARIANCE`, `TAX_VARIANCE`, `SETTLEMENT_CUTOFF`, `DELAYED_SETTLEMENT`, `INSTANT_SETTLEMENT_VARIANCE`, `REFUND_NETTED_LATER`, `PARTIAL_REFUND`, `MANGLED_UTR`, `MANGLED_NARRATION`, `DUPLICATE_LEDGER_ROW`, `DUPLICATE_BANK_CREDIT`, `DISPUTE_ADJUSTMENT`, `GENERAL_ADJUSTMENT`, `MISSING_ORDER`, `MISSING_PAYMENT`, `MISSING_SETTLEMENT`, `MISSING_BANK_CREDIT`, and `UNRESOLVABLE`.

## Generate artifacts

From the repository root:

```powershell
python scripts\generate_demo_data.py --dataset demo --output data\generated\demo
python scripts\generate_demo_data.py --dataset all --output data\generated
```

Each output directory contains `orders.json`, `payments.json`, `reconciliation_rows.json`, `bank_transactions.json`, and a separate `ground_truth.json`. The CLI uses no network, AI provider, credentials, or external dependency.
