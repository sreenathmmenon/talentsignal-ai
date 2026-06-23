"""TalentSignal evaluation subpackage.

Provides ranking-quality metrics, labeled synthetic datasets, and eval suites
used to measure any ranker against controlled ground truth across many JDs and
candidate-data shapes. This is both our quality instrument and the concrete
demonstration of the JD's "designing evaluation frameworks" requirement.
"""

__all__ = ["metrics", "datasets"]
