from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import Classification, Scenario, SpyglassRule


def replay_command(scenario: Scenario) -> str:
    if scenario.tool_mode == "vcs":
        compile_cmd = scenario.commands.get("compile", "vcs -full64 -sverilog -debug_access+all -f filelist.f")
        sim_cmd = scenario.commands.get("simulate", f"./simv +ntb_random_seed={scenario.seed}")
        return f"{compile_cmd}\n{sim_cmd}"
    return f"mock-replay --top {scenario.top} --seed {scenario.seed} --scenario {scenario.name}"


def render_markdown(scenario: Scenario, classification: Classification, rules: List[SpyglassRule]) -> str:
    first_failure = "n/a" if classification.first_failure_ns is None else f"{classification.first_failure_ns:.3f} ns"
    suspects = "\n".join(f"- `{s}`" for s in classification.suspects) or "- none"
    evidence = "\n".join(f"- {e}" for e in classification.evidence)
    actions = "\n".join(f"- {a}" for a in classification.recommended_actions)
    severe_rules = [r for r in rules if r.severity.lower() in {"high", "critical", "error"}]
    rule_rows = "\n".join(
        f"| {r.rule} | {r.severity} | `{r.object_name}` | {r.description} |" for r in severe_rules[:10]
    ) or "| n/a | n/a | n/a | n/a |"

    return f"""# GLS Failure Reconstruction Report: {scenario.name}

## Scenario

| Field | Value |
|---|---|
| Owner | {scenario.owner} |
| Top | `{scenario.top}` |
| Seed | `{scenario.seed}` |
| Tool mode | `{scenario.tool_mode}` |
| Replay command | `{replay_command(scenario).replace(chr(10), ' && ')}` |

## Classification

| Field | Value |
|---|---|
| Failure class | `{classification.failure_class}` |
| Confidence | `{classification.confidence:.2f}` |
| First failure timestamp | {first_failure} |

## Evidence

{evidence}

## Suspect signals / design objects

{suspects}

## High-severity SpyGlass-style correlations

| Rule | Severity | Object | Description |
|---|---:|---|---|
{rule_rows}

## Recommended next debug actions

{actions}
"""


def write_report(path: Path, scenario: Scenario, classification: Classification, rules: List[SpyglassRule]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(scenario, classification, rules))
    json_path = path.with_suffix(".json")
    json_path.write_text(json.dumps({
        "scenario": scenario.name,
        "failure_class": classification.failure_class,
        "confidence": classification.confidence,
        "first_failure_ns": classification.first_failure_ns,
        "suspects": classification.suspects,
        "evidence": classification.evidence,
        "recommended_actions": classification.recommended_actions,
    }, indent=2))
