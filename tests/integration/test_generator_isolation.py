from __future__ import annotations

import ast
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = REPOSITORY_ROOT / "engine" / "reconra"


def _import_paths(source_file: Path) -> list[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    paths: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            paths.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            paths.append(node.module)
    return paths


def test_engine_never_imports_generator_or_ground_truth() -> None:
    prohibited_imports: list[tuple[Path, str]] = []
    for source_file in ENGINE_ROOT.rglob("*.py"):
        for import_path in _import_paths(source_file):
            if import_path == "generator" or import_path.startswith("generator."):
                prohibited_imports.append((source_file, import_path))
            if import_path == "ground_truth" or import_path.startswith("ground_truth."):
                prohibited_imports.append((source_file, import_path))

    assert prohibited_imports == []
