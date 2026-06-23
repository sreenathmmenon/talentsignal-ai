"""Signal plugin framework — extensible intelligence beyond the core factors.

A *signal* is a pluggable scorer: given a candidate (and optionally the JD), it
returns a normalized 0..1 score plus evidence explaining it. Signals register
themselves, so new intelligence — background verification, GitHub-repo analysis,
reference checks — is added without touching the engine core.

    from talentsignal.signals import compute_signals, register_signal, Signal

    @register_signal
    class MySignal(Signal):
        name = "my_signal"
        def score(self, candidate, jd=None): ...

    results = compute_signals(candidate, jd)   # {name: SignalResult}

The core engine can optionally blend registered signals into scoring; surfaces
(UI/MCP/API) can surface them as extra evidence. This is the future-proofing
layer: the product grows by adding signals, not by rewrites.
"""
from __future__ import annotations

from .base import Signal, SignalResult, register_signal, compute_signals, list_signals
from . import builtin as _builtin  # noqa: F401  (registers built-in signals)

__all__ = ["Signal", "SignalResult", "register_signal", "compute_signals", "list_signals"]
