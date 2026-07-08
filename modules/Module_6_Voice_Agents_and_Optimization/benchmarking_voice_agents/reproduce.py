"""One-command reproduction of the benchmark results.

The pipeline has two phases; this script can run either or both:

  PHASE A — GATHER  (needs the live voice stack up: Postgres, Toolbox, A2A judge,
                     and both web servers — see README "Start the stack").
      run_bench.py drives BOTH architectures with one neutral stopwatch, reseeding
      the DB to a clean baseline before/between passes, and writes raw run records
      to runs/<arch>/qNN_rN.json.

  PHASE B — GRADE + REPORT  (needs only OPENAI_API_KEY in .env; no servers).
      each_question_acc.py   -> deterministic tool scores + LLM-judge response scores
      final_metrics.py       -> per-arch summary table
      compare.py             -> cross-arch table image + charts

Usage:
    python reproduce.py                 # Phase B only: grade (resume) -> report
    python reproduce.py --fresh         # wipe cached grades, re-judge everything, report
    python reproduce.py --with-bench    # Phase A + B  (SERVERS MUST BE UP)
    python reproduce.py --with-bench --fresh   # full clean reproduction from audio

Everything runs through THIS interpreter (sys.executable), so activate the single
venv that has requirements.txt installed and every step uses the same Python.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
ARCHS = ("cascade", "s2s")


def run(title: str, *script_args: str) -> None:
    print(f"\n{'=' * 72}\n>>> {title}\n{'=' * 72}", flush=True)
    subprocess.run([PY, *script_args], cwd=HERE, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Reproduce the voice-agent benchmark.")
    ap.add_argument("--with-bench", action="store_true",
                    help="run Phase A (run_bench.py) first — the live stack MUST be up")
    ap.add_argument("--fresh", action="store_true",
                    help="delete cached graded/ files so every run is re-judged")
    ap.add_argument("--repeats", type=int, default=3, help="runs per query for Phase A (default 3)")
    args = ap.parse_args()

    if args.with_bench:
        run("PHASE A — gather runs (both archs, fresh reseed)",
            "run_bench.py", "--arch", "both", "--reseed", "--repeats", str(args.repeats))

    if args.fresh:
        for arch in ARCHS:
            graded = HERE / "runs" / arch / "final_metric" / "graded"
            if graded.exists():
                shutil.rmtree(graded)
                print(f"  wiped {graded}")

    for arch in ARCHS:
        run(f"PHASE B1 — grade {arch}  (deterministic tools + LLM judge)",
            "each_question_acc.py", "--arch", arch)
    for arch in ARCHS:
        run(f"PHASE B2 — roll up final metrics: {arch}", "final_metrics.py", "--arch", arch)
    run("PHASE B3 — cross-arch comparison table + charts", "compare.py")

    print("\nDONE. Results:")
    print("  runs/<arch>/final_metric/  — per-question + final metrics (json/csv/md)")
    print("  comparison/                — comparison_table.png, comparison_chart.png, comparison_accuracy.png")


if __name__ == "__main__":
    main()
