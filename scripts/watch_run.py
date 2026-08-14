#!/usr/bin/env python3
"""Report whether a long run is alive, stalled, or dead, in one command.

A run of this size fails in three ways and only one of them is loud.

  dead      the driver exited on an error partway through. The files already written look
            perfectly healthy, so counting them tells you nothing
  stalled   the driver and the engine are both alive and producing nothing. Seen here when
            two engines shared one card, where throughput fell by a factor of four hundred.
            Progress is the test; the GPU counters are read only to describe a stall that
            has already been established, because the same counters read the same way during
            a healthy decode
  slow      running, but at a rate that will not finish in the time budgeted

None of the three announces itself. This checks all three against the previous call, so it
has to be run repeatedly to be worth anything -- every ten minutes from cron is the intent.

  python scripts/watch_run.py --phase P1a --expect 80
  python scripts/watch_run.py --phase P1b --expect 20 --quiet   # print only when wrong

Exit code is 0 when the run is healthy or finished and 1 when it needs attention, so a
caller can branch on it rather than read the text.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

STATE = os.environ.get("THEMIS_WATCH_STATE", ".watch_state.json")
DRIVER = os.environ.get("THEMIS_WATCH_DRIVER", "scripts/run_p1.py")
OUT_GLOB = "results/exp01/{phase}_*.jsonl"
LOG_GLOB = "results/exp01_*.log"
STALL_MINUTES = 12.0
ERROR_MARKERS = ("Traceback", "CalledProcessError", "ValidationError", "Value error",
                 "RuntimeError", "out of memory", "OutOfMemoryError", "Killed",
                 "unrecognized arguments", "PermissionError")


def alive(pattern):
    """Pids whose command line contains `pattern`, excluding anything to do with this check.

    pgrep -f matches full command lines, so a shell invoking this checker with the pattern
    anywhere in its own command line counts as a hit. That is not hypothetical: it made the
    first test of the dead-run branch report a healthy run.
    """
    r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
    out = []
    for pid in r.stdout.split():
        if not pid or int(pid) == os.getpid():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read().decode(errors="replace")
        except OSError:
            continue
        if "watch_run" in cmd:
            continue
        out.append(pid)
    return out


def gpu():
    """(utilisation, memory utilisation, memory used MiB, watts), or None if unavailable."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,utilization.memory,memory.used,"
                           "power.draw", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20, check=True)
    except Exception:  # noqa: BLE001
        return None
    try:
        return tuple(float(x) for x in r.stdout.strip().splitlines()[0].split(","))
    except (ValueError, IndexError):
        return None


def last_errors(n=4):
    logs = sorted(glob.glob(LOG_GLOB), key=os.path.getmtime)
    if not logs:
        return []
    with open(logs[-1], errors="replace") as f:
        lines = f.read().replace("\r", "\n").splitlines()
    hits = [l.strip()[:160] for l in lines if any(m in l for m in ERROR_MARKERS)]
    return hits[-n:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect", type=int, required=True, help="passes the run should produce")
    ap.add_argument("--phase", default="P1a", help="which phase's output files to count")
    ap.add_argument("--quiet", action="store_true", help="print only when something is wrong")
    args = ap.parse_args()
    # One state file per phase: sharing one would make every phase change look like a stall.
    state_path = STATE if args.phase == "P1a" else f"{STATE}.{args.phase}"

    now = time.time()
    done = len(glob.glob(OUT_GLOB.format(phase=args.phase)))
    pids = alive(DRIVER)
    prev = {}
    if os.path.isfile(state_path):
        try:
            prev = json.load(open(state_path))
        except json.JSONDecodeError:
            prev = {}
    json.dump({"t": now, "done": done, "alive": bool(pids)}, open(state_path, "w"))

    since = (now - prev["t"]) / 60 if "t" in prev else None
    gained = done - prev["done"] if "done" in prev else None

    problems = []
    if done >= args.expect:
        state = "COMPLETE"
    elif not pids:
        state = "DEAD"
        problems.append(f"driver is not running and only {done} of {args.expect} passes exist")
        for e in last_errors():
            problems.append(f"log says: {e}")
    else:
        state = "RUNNING"
        stalled = since is not None and since >= STALL_MINUTES and gained == 0
        if stalled:
            problems.append(f"no new pass in {since:.0f} min while the driver is alive")
            # Only meaningful once progress has already stopped. On this machine the same
            # reading -- high utilisation, almost no memory traffic -- is what a healthy
            # decode looks like between tqdm updates, so on its own it is a false alarm and
            # was one at 18 of 20 passes.
            g = gpu()
            if g and g[0] >= 90 and g[1] <= 5:
                problems.append(f"and the gpu is {g[0]:.0f}% busy with {g[1]:.0f}% memory "
                                f"traffic at {g[3]:.0f} W, so the engine is spinning rather "
                                f"than waiting")

    rate = (gained / since) if (since and gained) else None
    eta = f"{(args.expect - done) / rate:.0f} min" if rate else "unknown"

    if problems or not args.quiet:
        print(f"[{time.strftime('%H:%M')}] {state}  {done}/{args.expect} passes"
              + (f", +{gained} in {since:.0f} min, eta {eta}" if since is not None else ""))
        for p in problems:
            print(f"  ! {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
