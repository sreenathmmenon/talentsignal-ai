"""Built-in signals + future-facing extension stubs.

These show the framework working three ways:
  1. wrapping EXISTING engine intelligence as signals (hireability, consistency),
  2. a real new signal computed from data already present (github_activity),
  3. STUBS for the extensions the product roadmap names (background verification,
     github-repo deep analysis) — wired and registered, returning a clear
     "not yet connected" result, so adding the real implementation later is a
     one-function change with no engine impact.
"""
from __future__ import annotations

from typing import Any

from .base import Signal, SignalResult, register_signal


@register_signal
class HireabilitySignal(Signal):
    """Schema-driven availability/engagement/trust — is this person actually
    reachable and on the market? Wraps the existing schema_profile engine."""
    name = "hireability"
    weight = 1.0

    def score(self, candidate: dict[str, Any], jd: Any = None) -> SignalResult:
        from ..schema_profile import schema_signals, overall_hireability
        s = schema_signals(candidate)
        val = overall_hireability(candidate)
        ev = f"availability {s['availability']:.2f}, engagement {s['engagement']:.2f}, trust {s['trust']:.2f}"
        return SignalResult(self.name, val, ev, self.weight, details=s)


@register_signal
class ConsistencySignal(Signal):
    """Internal-consistency / honeypot signal — 1.0 = clean, lower = contradictions.
    Wraps the existing consistency auditor."""
    name = "consistency"
    weight = 1.0

    def score(self, candidate: dict[str, Any], jd: Any = None) -> SignalResult:
        from ..consistency_audit import audit_candidate
        rep = audit_candidate(candidate)
        val = max(0.0, 1.0 - rep.penalty)
        ev = "no contradictions" if not rep.flags else "; ".join(f.detail for f in rep.flags[:2])
        return SignalResult(self.name, val, ev, self.weight,
                            details={"flags": rep.codes, "is_impossible": rep.is_impossible})


@register_signal
class GithubActivitySignal(Signal):
    """Open-source/code-activity signal from the github_activity_score field if
    present. A real, working signal computed from data already in the profile."""
    name = "github_activity"
    weight = 0.5

    def applies_to(self, candidate: dict[str, Any], jd: Any = None) -> bool:
        sig = candidate.get("redrob_signals", {}) or {}
        return "github_activity_score" in sig

    def score(self, candidate: dict[str, Any], jd: Any = None) -> SignalResult:
        raw = float(candidate.get("redrob_signals", {}).get("github_activity_score", -1))
        if raw < 0:
            return SignalResult(self.name, 0.0, "no GitHub linked", self.weight)
        val = max(0.0, min(1.0, raw / 100.0))
        return SignalResult(self.name, val, f"GitHub activity score {raw:.0f}/100", self.weight)


# --- ROADMAP EXTENSION STUBS (wired, registered, ready for real impl) ----------

@register_signal
class BackgroundVerificationSignal(Signal):
    """ROADMAP: verify claimed employment/titles/credentials against external
    sources. Stub returns a neutral 'unverified' result with a clear hook so the
    real verification service can be dropped in without touching the engine."""
    name = "background_verification"
    weight = 0.0  # 0 weight until connected, so it never affects scoring yet

    def score(self, candidate: dict[str, Any], jd: Any = None) -> SignalResult:
        # Real implementation would call a verification provider here.
        claims = len(candidate.get("career_history", []) or [])
        return SignalResult(
            self.name, 0.5, f"{claims} employment claims pending verification (not yet connected)",
            self.weight, details={"status": "stub", "verifiable_claims": claims},
        )


@register_signal
class GithubRepoAnalysisSignal(Signal):
    """Real GitHub-repo analysis of a candidate's OWN linked public profile:
    public repos, total stars (peer validation), followers, languages, and recent
    activity → an explainable engineering-evidence score. Offline-safe (degrades
    to a clear 'not fetched' note). Weight 0.0 by default so it's a surfaced
    evidence signal a customer can opt to blend, not an automatic score change.
    """
    name = "github_repo_analysis"
    weight = 0.0

    def applies_to(self, candidate: dict[str, Any], jd: Any = None) -> bool:
        from ..github_analysis import find_github_username
        return bool(find_github_username(candidate))

    def score(self, candidate: dict[str, Any], jd: Any = None) -> SignalResult:
        from ..github_analysis import analyze_github
        # offline-safe: never fetches more than a few seconds, never raises.
        p = analyze_github(candidate, timeout=float(
            (candidate.get("_opts") or {}).get("github_timeout", 6.0)))
        return SignalResult(self.name, p.score, p.evidence, self.weight, details=p.to_dict())
