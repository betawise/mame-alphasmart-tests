#!/usr/bin/env python3
"""Run firmware-free tests against the explicitly selected MAME checkout."""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    here = Path(__file__).resolve().parent
    source = os.environ.get("MAME_SOURCE_ROOT")
    if not source:
        raise SystemExit("Set MAME_SOURCE_ROOT to the MAME source checkout under test.")
    source = Path(source).resolve()
    env = {**os.environ, "MAME_SOURCE_ROOT": str(source)}
    subprocess.run(["python3", "-m", "unittest", "discover", "-s",
                    "devices/mc68328", "-p", "test_*.py", "-v"],
                   cwd=here, env=env, check=True)
    with tempfile.TemporaryDirectory(prefix="mame-d11-test-") as directory:
        executable = str(Path(directory)/"pdiusbd11")
        subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        "-I", str(source/"src/mame/skeleton"),
                        str(here/"tests/usb/pdiusbd11.cpp"), "-o", executable], check=True)
        subprocess.run([executable], check=True)
    subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests/usb",
                    "-p", "test_*.py", "-v"], cwd=here, env=env, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
