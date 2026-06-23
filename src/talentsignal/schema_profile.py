"""Schema-driven signal engine.

Behavioral/availability/trust scoring should not hard-depend on Redrob's exact
23 signal fields — a real product ingests whatever a platform provides. This
module introspects the signals object on a candidate and maps it to a small set
of NORMALIZED, role-independent signal dimensions in [0,1]:

    availability  is the candidate actually reachable / on the market?
    engagement    are they active, responsive, in demand?
    trust         are they verified / credible?

It recognizes fields by name patterns (and known aliases), so the Redrob schema
and an alternate schema (e.g. reply_rate / days_since_login / available) both
produce comparable dimensions. Explicit Redrob fields are still read directly by
the scorer where present; this provides the general fallback and the
cross-schema comparability.
"""
from __future__ import annotations

import re
from typing import Any

# Field-name patterns -> (dimension, direction, normalizer)
# direction: +1 higher-is-better, -1 lower-is-better
# normalizer maps a raw value to [0,1].


def _frac(v: float, hi: float) -> float:
    try:
        return max(0.0, min(1.0, float(v) / hi))
    except (TypeError, ValueError):
        return 0.0


def _bool(v: Any) -> float:
    return 1.0 if bool(v) else 0.0


def _inv_months(v: float, cap: float = 6.0) -> float:
    """Recency: 0 months -> 1.0, >= cap months -> 0.0."""
    try:
        return max(0.0, min(1.0, 1.0 - float(v) / cap))
    except (TypeError, ValueError):
        return 0.0


def _inv_days(v: float, cap: float = 180.0) -> float:
    try:
        return max(0.0, min(1.0, 1.0 - float(v) / cap))
    except (TypeError, ValueError):
        return 0.0


def _inv_hours(v: float, cap: float = 240.0) -> float:
    try:
        return max(0.0, min(1.0, 1.0 - float(v) / cap))
    except (TypeError, ValueError):
        return 0.0


def _notice(v: float) -> float:
    try:
        d = float(v)
    except (TypeError, ValueError):
        return 0.5
    return 1.0 if d <= 30 else 0.7 if d <= 60 else 0.35 if d <= 90 else 0.15


# (regex on lowercased field name, dimension, fn) — first match wins per field.
_RULES: list[tuple[str, str, Any]] = [
    # availability
    (r"open.?to.?work|available|actively.?looking", "availability", _bool),
    (r"notice.?period|notice.?days", "availability", _notice),
    (r"willing.?to.?relocate|relocat", "availability", _bool),
    (r"last.?active|days.?since.?login", "availability", None),  # special-cased below
    # engagement
    (r"response.?rate|reply.?rate", "engagement", lambda v: _frac(v, 1.0)),
    (r"response.?time|reply.?hours|reply.?time", "engagement", _inv_hours),
    (r"saved.?by.?recruiters|recruiter.?saves", "engagement", lambda v: _frac(v, 15)),
    (r"profile.?views", "engagement", lambda v: _frac(v, 150)),
    (r"search.?appearance", "engagement", lambda v: _frac(v, 150)),
    (r"interview.?completion", "engagement", lambda v: _frac(v, 1.0)),
    (r"applications.?submitted", "engagement", lambda v: _frac(v, 10)),
    # trust
    (r"verified.?email|is.?email.?verified", "trust", _bool),
    (r"verified.?phone|is.?phone.?verified", "trust", _bool),
    (r"linkedin.?connected|external.?profile.?linked", "trust", _bool),
    (r"profile.?completeness|completeness", "trust", lambda v: _frac(v, 100)),
    (r"github.?activity", "trust", lambda v: _frac(max(0.0, v), 100) if _num(v) else 0.0),
    (r"offer.?acceptance", "trust", lambda v: _frac(max(0.0, v), 1.0) if _num(v) else 0.0),
    (r"endorsements.?received", "trust", lambda v: _frac(v, 100)),
]


def _num(v: Any) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def schema_signals(candidate: dict[str, Any]) -> dict[str, float]:
    """Return normalized {availability, engagement, trust} in [0,1] from whatever
    signal fields the candidate has. Robust to unknown schemas: unrecognized
    fields are ignored; missing dimensions default to a neutral 0.5."""
    signals = candidate.get("redrob_signals") or candidate.get("signals") or {}
    buckets: dict[str, list[float]] = {"availability": [], "engagement": [], "trust": []}

    for raw_name, value in signals.items():
        name = str(raw_name).lower()
        for pattern, dim, fn in _RULES:
            if re.search(pattern, name):
                if fn is None:
                    # recency fields: months vs days by name
                    if "day" in name:
                        buckets[dim].append(_inv_days(value))
                    else:
                        buckets[dim].append(_recency_from_date(value))
                else:
                    buckets[dim].append(float(fn(value)))
                break

    return {dim: round(sum(vals) / len(vals), 4) if vals else 0.5 for dim, vals in buckets.items()}


def _recency_from_date(value: Any) -> float:
    """last_active_date (YYYY-MM-DD) -> recency in [0,1] vs the reference date."""
    m = re.match(r"(\d{4})-(\d{2})", str(value or ""))
    if not m:
        return 0.5
    y, mo = int(m.group(1)), int(m.group(2))
    months = (2026 - y) * 12 + (6 - mo)
    return _inv_months(max(0, months))


def overall_hireability(candidate: dict[str, Any]) -> float:
    """A single 0..1 hireability blend from the three dimensions, schema-agnostic."""
    s = schema_signals(candidate)
    return round(0.40 * s["availability"] + 0.35 * s["engagement"] + 0.25 * s["trust"], 4)
