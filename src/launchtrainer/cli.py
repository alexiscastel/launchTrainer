from __future__ import annotations

import argparse
import json
from pathlib import Path

from .detection import DetectionResult, detect_launch
from .metrics import MetricResult, compute_metrics
from .parser import CSVDataError, CSVSchemaError, LaunchTrainerError, parse_csv
from .signals import centered_moving_average, climb_rates, estimate_sample_period


def analyze_csv(csv_path: str | Path) -> dict:
    path = Path(csv_path)
    samples = parse_csv(path)

    times_s = [sample.t_s for sample in samples]
    raw_altitudes_m = [sample.alt_m for sample in samples]
    smoothed_altitudes_m = centered_moving_average(raw_altitudes_m, window=3)
    sample_period_s = estimate_sample_period(samples)
    climb_rates_mps = climb_rates(times_s, smoothed_altitudes_m)

    detection = detect_launch(samples, smoothed_altitudes_m, sample_period_s)
    metrics = compute_metrics(samples, smoothed_altitudes_m, climb_rates_mps, detection)

    warnings = list(detection.warnings)
    status = "warning" if warnings else "ok"

    return build_payload(path, detection, metrics, status, warnings)


def build_payload(
    source_path: Path,
    detection: DetectionResult,
    metrics: MetricResult,
    status: str,
    warnings: list[str],
) -> dict:
    return {
        "source_file": str(source_path),
        "status": status,
        "detection": {
            "method": detection.method,
            "confidence": detection.confidence,
            "start_time_s": round(detection.start_time_s, 3),
            "end_time_s": round(detection.end_time_s, 3),
            "sample_period_s": round(detection.sample_period_s, 3),
        },
        "metrics": {
            "launch_height_m": round(metrics.launch_height_m, 3),
            "time_to_apex_s": round(metrics.time_to_apex_s, 3),
            "max_climb_rate_mps": round(metrics.max_climb_rate_mps, 3),
        },
        "warnings": warnings,
    }


def build_error_payload(source_path: Path, message: str) -> dict:
    return {
        "source_file": str(source_path),
        "status": "error",
        "detection": {
            "method": "auto_v1",
            "confidence": "low",
            "start_time_s": 0.0,
            "end_time_s": 0.0,
            "sample_period_s": 0.0,
        },
        "metrics": {
            "launch_height_m": 0.0,
            "time_to_apex_s": 0.0,
            "max_climb_rate_mps": 0.0,
        },
        "warnings": [message],
    }


def print_summary(payload: dict) -> None:
    detection = payload["detection"]
    metrics = payload["metrics"]

    print(f"Source: {payload['source_file']}")
    print(f"Status: {payload['status']}")
    print(
        "Detection: "
        f"{detection['method']} | confidence={detection['confidence']} | "
        f"start={detection['start_time_s']:.3f}s | end={detection['end_time_s']:.3f}s | "
        f"sample_period={detection['sample_period_s']:.3f}s"
    )
    print(
        "Metrics: "
        f"launch_height_m={metrics['launch_height_m']:.3f}, "
        f"time_to_apex_s={metrics['time_to_apex_s']:.3f}, "
        f"max_climb_rate_mps={metrics['max_climb_rate_mps']:.3f}"
    )

    if payload["warnings"]:
        print("Warnings:")
        for warning in payload["warnings"]:
            print(f"- {warning}")


def write_json(payload: dict, json_path: str | Path) -> None:
    path = Path(json_path)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="launchtrainer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a telemetry CSV.")
    analyze_parser.add_argument("csv_path", help="Path to the telemetry CSV file.")
    analyze_parser.add_argument(
        "--json-out",
        help="Optional path for structured JSON output.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command != "analyze":
        parser.error(f"unsupported command: {args.command}")

    source_path = Path(args.csv_path)

    try:
        payload = analyze_csv(source_path)
        print_summary(payload)
        if args.json_out:
            write_json(payload, args.json_out)
        return 0
    except (CSVSchemaError, CSVDataError, LaunchTrainerError) as exc:
        payload = build_error_payload(source_path, str(exc))
        print_summary(payload)
        if args.json_out:
            write_json(payload, args.json_out)
        return 1
