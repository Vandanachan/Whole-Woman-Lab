"""Immutable-by-convention data objects shared across Engine 1.

Plain dataclasses keep the engine dependency-light and deterministic. Frozen
where the object is a settled fact/output; mutable only for the live Hypothesis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Modality = Literal["symptom", "tongue", "pulse", "history", "lab", "htma"]


@dataclass(frozen=True, slots=True)
class Fact:
    """A normalised, atomic clinical truth. Not a diagnosis."""
    code: str
    label: str
    modality: str
    etype: str
    objective: bool
    quality: float  # data-confidence in [0,1]


@dataclass(frozen=True, slots=True)
class Evidence:
    """A Fact elevated into the reasoning system with its salience."""
    code: str
    label: str
    objective: bool
    quality: float


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    """Directed edge: an evidence code contributing to a hypothesis."""
    evidence_code: str
    pattern_id: str
    weight: float
    objective: bool


@dataclass(slots=True)
class Hypothesis:
    """A live, competing candidate pattern. Mutable during scoring."""
    pattern_id: str
    name: str
    thermal: str
    excess_deficiency: str
    can_be_root: bool
    max_possible: float
    treatment_principle: str
    formulas: list[str]
    caution: str | None = None
    raw_score: float = 0.0
    supporting: list[str] = field(default_factory=list)
    supporting_objective_weight: float = 0.0
    supporting_total_weight: float = 0.0
    unmet_expected: list[str] = field(default_factory=list)

    @property
    def normalized(self) -> float:
        if self.max_possible <= 0:
            return 0.0
        return round(min(1.0, self.raw_score / self.max_possible), 4)


@dataclass(frozen=True, slots=True)
class ConfidenceComponent:
    name: str
    value: float
    weight: float

    @property
    def contribution(self) -> float:
        return round(self.value * self.weight, 4)


@dataclass(frozen=True, slots=True)
class Confidence:
    value: float
    band: str
    components: tuple[ConfidenceComponent, ...]
    threshold: float

    @property
    def meets_threshold(self) -> bool:
        return self.value >= self.threshold


@dataclass(frozen=True, slots=True)
class Contradiction:
    kind: str
    pattern_a: str
    pattern_b: str
    description: str


@dataclass(frozen=True, slots=True)
class Resolution:
    kind: str
    strategy: str
    status: str
    winner: str | None
    suppressed: str | None
    coexist: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class ProgressionEdge:
    src: str
    dst: str
    relation: str
    likelihood: float
    mechanism: str


@dataclass(frozen=True, slots=True)
class ProgressionPath:
    roots: tuple[str, ...]
    branches: tuple[str, ...]
    edges: tuple[ProgressionEdge, ...]
    projected_next: tuple[str, ...]
    reversibility: str


@dataclass(frozen=True, slots=True)
class DifferentialItem:
    rank: int
    pattern_id: str
    name: str
    status: str  # present | tendency
    confidence: float
    normalized_score: float
    key_evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SafetyFlag:
    rule_id: str
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class ReasoningStep:
    stage: str
    description: str


@dataclass(frozen=True, slots=True)
class Diagnosis:
    pattern_id: str
    name: str
    role: str  # root | branch | co-primary
    confidence: Confidence
    priority_level: str
    priority_numeric: float
    evidence: tuple[str, ...]
    treatment_principle: str
    formulas: tuple[str, ...]
    caution: str | None
    explanation: str
