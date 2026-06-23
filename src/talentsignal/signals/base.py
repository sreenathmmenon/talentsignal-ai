"""Signal interface + registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SignalResult:
    name: str
    score: float                     # 0..1 normalized
    evidence: str = ""               # human-readable why
    weight: float = 1.0              # relative importance (configurable)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "score": round(self.score, 4), "evidence": self.evidence,
                "weight": self.weight, "details": self.details}


class Signal:
    """Base class for a pluggable signal. Subclass and set `name`, implement
    `score(candidate, jd) -> SignalResult`."""
    name: str = "signal"
    weight: float = 1.0

    def applies_to(self, candidate: dict[str, Any], jd: Any = None) -> bool:
        return True

    def score(self, candidate: dict[str, Any], jd: Any = None) -> SignalResult:  # pragma: no cover
        raise NotImplementedError


_REGISTRY: dict[str, "Signal"] = {}


def register_signal(cls):
    """Class decorator: instantiate and register a Signal subclass."""
    inst = cls()
    _REGISTRY[inst.name] = inst
    return cls


def list_signals() -> list[str]:
    return sorted(_REGISTRY)


def compute_signals(candidate: dict[str, Any], jd: Any = None,
                    only: list[str] | None = None) -> dict[str, SignalResult]:
    """Run all (or a subset of) registered signals over a candidate."""
    out: dict[str, SignalResult] = {}
    for name, sig in _REGISTRY.items():
        if only is not None and name not in only:
            continue
        try:
            if sig.applies_to(candidate, jd):
                out[name] = sig.score(candidate, jd)
        except Exception as exc:  # noqa: BLE001 - a bad signal must not break ranking
            out[name] = SignalResult(name=name, score=0.0, evidence=f"(signal error: {exc})")
    return out


def blended_signal_score(results: dict[str, SignalResult]) -> float:
    """Weighted average of signal scores (0..1), for optional blending into scoring."""
    if not results:
        return 0.0
    tw = sum(r.weight for r in results.values()) or 1.0
    return round(sum(r.score * r.weight for r in results.values()) / tw, 4)
