#!/usr/bin/env python3
# license:BSD-3-Clause
"""Run ST7565R device and Neo firmware regressions using MAME's Lua API."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mame", default="./neodiag")
    parser.add_argument("--rompath", default="roms")
    parser.add_argument("--output", type=Path, help="new directory for logs and disposable state")
    args = parser.parse_args()
    output = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix="st7565-results-"))
    if args.output:
        output.mkdir(parents=True, exist_ok=False)
    print(f"Artifacts: {output}")
    executable = Path(args.mame).resolve()
    rompath = os.pathsep.join(str(Path(p).resolve()) for p in args.rompath.split(os.pathsep))
    for script, marker in [("parallel.lua", "PASS ST7565R"), ("neo.lua", "PASS Neo LCD")]:
        temporary = output / Path(script).stem
        temporary.mkdir()
        command = [str(executable), "asneo", "-rompath", rompath,
                   "-video", "none", "-sound", "none", "-nothrottle",
                   "-seconds_to_run", "30", "-inipath", str(temporary),
                   "-cfg_directory", str(temporary), "-nvram_directory", str(temporary),
                   "-snapshot_directory", str(temporary / "snap"),
                   "-state_directory", str(temporary / "state"),
                   "-autoboot_script", str(Path(__file__).with_name(script).resolve())]
        if script == "parallel.lua":
            command += ["-debug", "-debugger", "none"]
        (temporary / "command.json").write_text(json.dumps(command, indent=2) + "\n")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120,
                                    env={**os.environ, "SDL_VIDEODRIVER": "dummy",
                                         "SDL_AUDIODRIVER": "dummy"})
        except subprocess.TimeoutExpired as exc:
            for name, data in [("stdout", exc.stdout), ("stderr", exc.stderr)]:
                (temporary / f"{name}.log").write_bytes(
                    data if isinstance(data, bytes) else (data or "").encode())
            (temporary / "result.json").write_text(
                json.dumps(dict(passed=False, error="timeout", seconds=120)) + "\n")
            print(f"FAIL: {script} timed out; see {temporary}")
            return 1
        (temporary / "stdout.log").write_text(result.stdout)
        (temporary / "stderr.log").write_text(result.stderr)
        (temporary / "result.json").write_text(json.dumps(dict(exit=result.returncode, passed=result.returncode == 0 and marker in result.stdout and "FAIL" not in result.stdout)) + "\n")
        print(result.stdout, end="")
        if result.returncode or marker not in result.stdout or "FAIL" in result.stdout:
            print(result.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
