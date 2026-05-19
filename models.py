from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ArtifactSet:
    vcs_log: Path
    waveform_markers: Path
    spyglass_report: Path


@dataclass
class Scenario:
    name: str
    root: Path
    owner: str
    seed: int
    top: str
    tool_mode: str
    failure_class_hint: Optional[str]
    artifacts: ArtifactSet
    commands: Dict[str, str] = field(default_factory=dict)


@dataclass
class WaveMarker:
    time_ns: float
    signal: str
    value: str
    note: str


@dataclass
class SpyglassRule:
    rule: str
    severity: str
    object_name: str
    description: str


@dataclass
class Classification:
    failure_class: str
    confidence: float
    first_failure_ns: Optional[float]
    suspects: List[str]
    evidence: List[str]
    recommended_actions: List[str]
