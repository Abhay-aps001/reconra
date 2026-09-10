# Local release verification checklist

Run these commands from the repository root before a deliberate deployment or release:

    ruff check .
    mypy engine apps/api
    pytest -q

    pnpm --dir apps/web test
    pnpm --dir apps/web lint
    pnpm --dir apps/web exec tsc --noEmit
    pnpm --dir apps/web build
    pnpm --dir apps/web exec playwright test --workers=1

    python scripts/saved_benchmark.py
    git diff --check
    git status --short

Confirm that the saved benchmark remains labeled saved/non-live, its scoring availability is truthful, no secrets are present, Razorpay remains Test Mode read-only, and no deployment URL has been invented.
