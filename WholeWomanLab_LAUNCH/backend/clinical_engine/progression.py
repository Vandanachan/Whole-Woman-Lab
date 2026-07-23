"""Progression layer — root vs branch and where the picture is heading.

Uses the pattern-progression graph: if an active pattern is produced by another
active pattern (has an incoming edge from it), it is a *branch*; an active
pattern that is itself a source (and eligible) is a *root*. Outgoing edges to
not-yet-active patterns are the projected next steps.
"""
from __future__ import annotations

from .models import Hypothesis, ProgressionEdge, ProgressionPath


def build_progression(
    active: list[str], hyps: dict[str, Hypothesis], edges_raw: list[dict]
) -> ProgressionPath:
    active_set = set(active)
    edges = [ProgressionEdge(e["src"], e["dst"], e["relation"], float(e["likelihood"]), e["mechanism"])
             for e in edges_raw if e["src"] in active_set]
    incoming_from_active = {e.dst for e in edges if e.dst in active_set}

    roots = tuple(sorted(
        p for p in active
        if hyps[p].can_be_root and p not in incoming_from_active
    ))
    branches = tuple(sorted(p for p in active if p in incoming_from_active))
    projected = tuple(sorted({e.dst for e in edges if e.dst not in active_set}))

    # deficiency/stagnation roots are functional & largely reversible
    reversibility = "partially_reversible"
    if roots and all(hyps[r].excess_deficiency in {"deficiency", "excess"} for r in roots):
        reversibility = "reversible" if any(hyps[r].excess_deficiency == "excess" for r in roots) \
            else "partially_reversible"

    return ProgressionPath(
        roots=roots, branches=branches, edges=tuple(edges),
        projected_next=projected, reversibility=reversibility,
    )
