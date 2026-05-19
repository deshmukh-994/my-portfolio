from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console

from .classifier import classify_failure
from .io import load_scenario, read_log, read_spyglass_rules, read_wave_markers
from .reporter import render_markdown, write_report

console = Console()


def run_one(scenario_file: Path, out: Path) -> None:
    scenario = load_scenario(scenario_file)
    log_text = read_log(scenario.artifacts.vcs_log)
    markers = read_wave_markers(scenario.artifacts.waveform_markers)
    rules = read_spyglass_rules(scenario.artifacts.spyglass_report)
    classification = classify_failure(log_text, markers, rules)
    write_report(out, scenario, classification, rules)
    console.print(f"[green]Generated[/green] {out}")
    console.print(f"Classified {scenario.name} as [bold]{classification.failure_class}[/bold] confidence={classification.confidence:.2f}")


def batch(root: Path, out: Path) -> None:
    scenario_files = sorted(root.glob("*/scenario.yaml"))
    if not scenario_files:
        raise SystemExit(f"No scenario.yaml files found under {root}")
    sections = ["# GLS Failure Reconstruction Batch Summary\n"]
    for idx, scenario_file in enumerate(scenario_files, start=1):
        scenario = load_scenario(scenario_file)
        classification = classify_failure(
            read_log(scenario.artifacts.vcs_log),
            read_wave_markers(scenario.artifacts.waveform_markers),
            read_spyglass_rules(scenario.artifacts.spyglass_report),
        )
        sections.append(
            f"## {idx}. {scenario.name}\n\n"
            f"- Failure class: `{classification.failure_class}`\n"
            f"- Confidence: `{classification.confidence:.2f}`\n"
            f"- First failure: `{classification.first_failure_ns}` ns\n"
            f"- Suspects: {', '.join(classification.suspects) or 'none'}\n"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(sections))
    console.print(f"[green]Generated[/green] {out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay and classify GLS failure scenarios")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run", help="Replay one scenario")
    run_p.add_argument("scenario", type=Path)
    run_p.add_argument("--out", type=Path, default=Path("reports/report.md"))
    batch_p = sub.add_parser("batch", help="Replay all scenarios under a directory")
    batch_p.add_argument("root", type=Path)
    batch_p.add_argument("--out", type=Path, default=Path("reports/summary.md"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.cmd == "run":
        run_one(args.scenario, args.out)
    elif args.cmd == "batch":
        batch(args.root, args.out)


if __name__ == "__main__":
    main()
