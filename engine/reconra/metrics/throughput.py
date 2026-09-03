"""Nanosecond-based throughput measurement without binary floating-point rates."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Throughput:
    record_count: int
    elapsed_ns: int

    @property
    def records_per_second(self) -> tuple[int, int]:
        if self.elapsed_ns <= 0:
            return 0, 1
        return self.record_count * 1_000_000_000, self.elapsed_ns
