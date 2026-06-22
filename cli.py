"""
Command-line interface for the Ammeter Testing Framework.

Run measurement tests, override sampling parameters, and inspect saved runs
without editing config.yaml.

Examples:
    py cli.py run                          # test all ammeters (config defaults)
    py cli.py run -a greenlee -n 50 -f 10  # 50 samples @ 10 Hz, greenlee only
    py cli.py run --errors                 # enable error simulation
    py cli.py run --no-plots -o /tmp/out   # skip plots, custom output dir
    py cli.py list                         # list saved runs
    py cli.py show results/<run_folder>    # print a saved run's summary
"""
import argparse
import os
import sys

# Make the project root importable regardless of the current working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.testing.test_framework import AmmeterTestFramework
from src.testing.result import TestResult, list_results
from src.utils.config import DEFAULT_CONFIG_PATH


def _print_stats(name: str, result: TestResult) -> None:
    s = result.statistics
    print(f"\n{name} (run {result.run_id}):")
    if s.get("count", 0) == 0:
        print("  no valid samples collected.")
        return
    print(f"  samples : {s['count']}")
    print(f"  mean    : {s['mean']:.4f} A")
    print(f"  median  : {s['median']:.4f} A")
    print(f"  std dev : {s['std_dev']:.4f} A")
    print(f"  min/max : {s['min']:.4f} / {s['max']:.4f} A")
    print(f"  CV      : {s['coefficient_of_variation']:.4f}")


def _apply_overrides(framework: AmmeterTestFramework, args: argparse.Namespace) -> None:
    """Apply CLI flags on top of the loaded config before running."""
    sampling = framework.config["testing"]["sampling"]
    if args.count is not None:
        sampling["measurements_count"] = args.count
    if args.duration is not None:
        sampling["total_duration_seconds"] = args.duration
    if args.frequency is not None:
        sampling["sampling_frequency_hz"] = args.frequency
    if args.errors:
        framework.config.setdefault("error_simulation", {})["enabled"] = True
    if args.no_plots:
        framework.config.setdefault("analysis", {}).setdefault("visualization", {})["enabled"] = False
    if args.output:
        framework.config.setdefault("result_management", {})["output_dir"] = args.output


def cmd_run(args: argparse.Namespace) -> int:
    framework = AmmeterTestFramework(args.config, start_emulators=False)
    _apply_overrides(framework, args)
    framework.start_emulators()

    results = framework.run_all(args.ammeter or None)
    for name, result in results.items():
        _print_stats(name, result)

    comparison = framework.compare(results)
    if comparison and comparison.get("ranking"):
        print("\n=== Cross-ammeter reliability (lower CV = more reliable) ===")
        print(comparison["table"])
        print(f"\nMost reliable: {comparison['most_reliable']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    runs = list_results(args.output)
    if not runs:
        print(f"No saved runs found in '{args.output}'.")
        return 0
    print(f"Saved runs in '{args.output}' (newest first):")
    for run_dir in runs:
        print(f"  {run_dir}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    if not os.path.exists(args.path):
        print(f"Path not found: {args.path}", file=sys.stderr)
        return 1
    result = TestResult.load(args.path)
    _print_stats(result.ammeter_type, result)
    print(f"\n  command : {result.command}")
    print(f"  port    : {result.port}")
    print(f"  when    : {result.timestamp}")
    print(f"  plan    : {result.sampling_plan}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Ammeter Testing Framework command-line interface.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    run = sub.add_parser("run", help="run measurement tests against the ammeters")
    run.add_argument("-a", "--ammeter", action="append", metavar="NAME",
                     help="ammeter to test (repeatable); default: all configured")
    run.add_argument("-n", "--count", type=int, help="number of samples")
    run.add_argument("-d", "--duration", type=float, help="total duration (seconds)")
    run.add_argument("-f", "--frequency", type=float, help="sampling frequency (Hz)")
    run.add_argument("--errors", action="store_true", help="enable error simulation")
    run.add_argument("--no-plots", action="store_true", help="disable plot generation")
    run.add_argument("-o", "--output", help="output directory for results")
    run.add_argument("-c", "--config", default=DEFAULT_CONFIG_PATH, help="path to config.yaml")
    run.set_defaults(func=cmd_run)

    # list
    lst = sub.add_parser("list", help="list saved test runs")
    lst.add_argument("-o", "--output", default="results", help="results directory")
    lst.set_defaults(func=cmd_list)

    # show
    show = sub.add_parser("show", help="print a saved run's summary")
    show.add_argument("path", help="run folder or result.json path")
    show.set_defaults(func=cmd_show)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
