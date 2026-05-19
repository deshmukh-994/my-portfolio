from __future__ import annotations

import csv
from pathlib import Path
from typing import List

import yaml

from .models import ArtifactSet, Scenario, SpyglassRule, WaveMarker


def load_scenario(path: str | Path) -> Scenario:
    scenario_path = Path(path).resolve()
    data = yaml.safe_load(scenario_path.read_text())
    root = scenario_path.parent
    artifacts = data.get("artifacts", {})
    return Scenario(
        name=data["name"],
        root=root,
        owner=data.get("owner", "unknown"),
        seed=int(data.get("seed", 0)),
        top=data.get("top", "tb_top"),
        tool_mode=data.get("tool_mode", "mock"),
        failure_class_hint=data.get("failure_class_hint"),
        artifacts=ArtifactSet(
            vcs_log=root / artifacts.get("vcs_log", "vcs.log"),
            waveform_markers=root / artifacts.get("waveform_markers", "waveform_markers.csv"),
            spyglass_report=root / artifacts.get("spyglass_report", "spyglass_rules.csv"),
        ),
        commands=data.get("commands", {}),
    )


def read_wave_markers(path: Path) -> List[WaveMarker]:
    with path.open(newline="") as f:
        rows = csv.DictReader(f)
        return [
            WaveMarker(
                time_ns=float(row["time_ns"]),
                signal=row["signal"],
                value=row["value"],
                note=row.get("note", ""),
            )
            for row in rows
        ]


def read_spyglass_rules(path: Path) -> List[SpyglassRule]:
    with path.open(newline="") as f:
        rows = csv.DictReader(f)
        return [
            SpyglassRule(
                rule=row["rule"],
                severity=row["severity"],
                object_name=row["object_name"],
                description=row.get("description", ""),
            )
            for row in rows
        ]


def read_log(path: Path) -> str:
    return path.read_text(errors="replace")
