from pathlib import Path


def test_ci_enforces_secretless_python_and_frontend_quality_gates() -> None:
    workflow = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    for expected in (
        "pull_request:",
        "branches: [main]",
        "contents: read",
        "ruff check .",
        "mypy engine apps/api",
        "pytest -q",
        "pnpm install --frozen-lockfile",
        "pnpm --dir apps/web test",
        "pnpm --dir apps/web lint",
        "pnpm --dir apps/web exec tsc --noEmit",
        "pnpm --dir apps/web build",
        "playwright install --with-deps chromium",
        "playwright test --workers=1",
    ):
        assert expected in workflow

    assert "secrets." not in workflow
