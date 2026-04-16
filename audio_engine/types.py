from dataclasses import dataclass


@dataclass
class Segment:
    start_sec: int
    end_sec: int | None
    title: str
    strategy: str
    confidence: float | None = None
