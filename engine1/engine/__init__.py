"""WholeWomanLab — Engine 1: Clinical Reasoning Engine.

Deterministic, explainable clinical reasoning. No LLM inference anywhere in
this package; the LLM (elsewhere) only renders the structured output to prose.
"""
from .reasoning import Engine, EngineResult  # noqa: F401

__version__ = "1.0.0"
