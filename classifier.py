from __future__ import annotations

import re
from typing import Iterable, List, Optional

from .models import Classification, SpyglassRule, WaveMarker

X_TOKENS = {"x", "X", "1'bx", "1'bX", "unknown", "UNKNOWN"}
TIMING_PATTERNS = ["setup", "hold", "recovery", "removal", "SDF", "timing violation"]


def _first_time(markers: Iterable[WaveMarker], predicate) -> Optional[float]:
    times = [m.time_ns for m in markers if predicate(m)]
    return min(times) if times else None


def classify_failure(log_text: str, markers: List[WaveMarker], rules: List[SpyglassRule]) -> Classification:
    log_lower = log_text.lower()
    x_markers = [m for m in markers if m.value in X_TOKENS or "x-prop" in m.note.lower() or "unknown" in m.note.lower()]
    timing_markers = [m for m in markers if "timing" in m.note.lower() or "glitch" in m.note.lower()]
    timing_log_hits = [p for p in TIMING_PATTERNS if p.lower() in log_lower]

    x_rule_hits = [r for r in rules if re.search(r"x|reset|init|undriven|unconnected", r.description, re.I)]
    timing_rule_hits = [r for r in rules if re.search(r"clock|cdc|constraint|multicycle|false path|timing", r.description, re.I)]

    evidence: List[str] = []
    suspects: List[str] = []
    recommended: List[str] = []

    if x_markers or x_rule_hits:
        failure_class = "x_propagation"
        confidence = min(0.95, 0.55 + 0.1 * len(x_markers) + 0.08 * len(x_rule_hits))
        first_failure = _first_time(markers, lambda m: m in x_markers)
        suspects = sorted({m.signal for m in x_markers} | {r.object_name for r in x_rule_hits})
        evidence.append(f"Detected {len(x_markers)} waveform markers with unknown/X values.")
        evidence.append(f"Correlated {len(x_rule_hits)} SpyGlass-style reset/init/undriven rule hits.")
        recommended = [
            "Backtrace first X source from the earliest suspect flop or net.",
            "Compare reset sequencing between RTL and netlist simulation.",
            "Check synthesis tie-off, undriven-net, and scan insertion deltas.",
        ]
    elif timing_markers or timing_log_hits or timing_rule_hits:
        failure_class = "timing_mismatch"
        confidence = min(0.94, 0.55 + 0.12 * len(timing_markers) + 0.1 * len(timing_log_hits) + 0.06 * len(timing_rule_hits))
        first_failure = _first_time(markers, lambda m: m in timing_markers)
        suspects = sorted({m.signal for m in timing_markers} | {r.object_name for r in timing_rule_hits})
        evidence.append(f"Detected {len(timing_markers)} waveform timing/glitch markers.")
        evidence.append(f"Detected {len(timing_log_hits)} timing-related log signatures.")
        evidence.append(f"Correlated {len(timing_rule_hits)} SpyGlass-style timing/CDC/constraint rule hits.")
        recommended = [
            "Inspect SDF annotation coverage and min/typ/max corner alignment.",
            "Check clock-domain crossing synchronizers and generated-clock constraints.",
            "Re-run failing seed with expanded timing checks around the first mismatch window.",
        ]
    else:
        failure_class = "unclassified"
        confidence = 0.35
        first_failure = min((m.time_ns for m in markers), default=None)
        suspects = sorted({m.signal for m in markers[:5]})
        evidence.append("No strong X-propagation or timing signature was detected.")
        recommended = [
            "Add more waveform checkpoints around the first scoreboard mismatch.",
            "Include RTL-vs-GLS transaction comparison metadata.",
        ]

    return Classification(
        failure_class=failure_class,
        confidence=round(confidence, 2),
        first_failure_ns=first_failure,
        suspects=suspects,
        evidence=evidence,
        recommended_actions=recommended,
    )
