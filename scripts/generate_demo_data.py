from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _parse_args(dataset_choices: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic Reconra synthetic datasets."
    )
    parser.add_argument(
        "--dataset",
        choices=[*dataset_choices, "all"],
        required=True,
        help="Dataset role to generate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "generated",
        help="Directory for generated JSON artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    from generator.src.artifacts import write_dataset_artifacts
    from generator.src.config import DatasetRole
    from generator.src.roles import generate_dataset

    args = _parse_args([role.value for role in DatasetRole])
    roles = list(DatasetRole) if args.dataset == "all" else [DatasetRole(args.dataset)]
    for role in roles:
        destination = args.output / role.value if args.dataset == "all" else args.output
        write_dataset_artifacts(generate_dataset(role), destination)
        print(f"generated {role.value}: {destination}")


if __name__ == "__main__":
    main()
