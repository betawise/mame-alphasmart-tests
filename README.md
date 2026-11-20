# AlphaSmart MAME regression tests

Device and emulator regression tests kept outside the MAME source tree so
contributors can share them independently of upstream test placement.
**Betawise feature tests stay in Betawise.** This repository contains no
production emulation code, ROMs, firmware, MAME binaries, or saved sessions.

## Requirements

- Python 3.11+ and a C++17 compiler (`c++`).
- A MAME source checkout containing the AlphaSmart changes under test.
- For LCD/Palm integration tests: suitable MAME builds and your own ROMs.
- Pillow for the optional Palm comparison (`python3 -m pip install Pillow`).

Set the source checkout explicitly; tests read its actual implementation rather
than a copied implementation bundled here:

```bash
export MAME_SOURCE_ROOT=/absolute/path/to/mame
python3 run.py
```

The default runs the firmware-free checks below. USB/IP tests open loopback
sockets and need local socket permissions. A missing implementation is a failure,
not a silently skipped test. Use a source revision with both the interrupt fix
and USB support; the initial USB baseline was `6a7b11dffbd` in
[isotherm/mame](https://github.com/isotherm/mame/tree/alphasmart).
The import validation section below records the component-test baseline.

## Firmware-free tests

| Suite | What it exercises |
|---|---|
| `devices/mc68328/test_mc68328_interrupts.py` | Compiles the production interrupt-update methods into a small CPU-line fixture; checks ISR/IPR visibility, repeated masking/unmasking, and shared interrupt levels. |
| `tests/usb/pdiusbd11.cpp` | Includes the production D11 header and drives I2C pins, endpoint buffers/status, SETUP, interrupts, and reset. |
| `tests/usb/test_usbip.py` | Imports the production Python bridge and checks USB/IP discovery/import, transfers, unlink, and cancellation synchronization through loopback sockets with a simulated firmware peer. |

Run them individually from this repository root:

```bash
python3 -m unittest discover -s devices/mc68328 -p 'test_*.py' -v
c++ -std=c++17 -Wall -Wextra -Werror \
  -I "$MAME_SOURCE_ROOT/src/mame/skeleton" tests/usb/pdiusbd11.cpp \
  -o /tmp/pdiusbd11-test
/tmp/pdiusbd11-test
python3 -m unittest discover -s tests/usb -p 'test_*.py' -v
```

These are bounded component tests. They do not prove full SoC correctness,
firmware enumeration, Linux VHCI attachment, or physical hardware behavior.

## ST7565R / Neo LCD integration

Build a MAME checkout with the ST7565R device and `asneo` driver:

```bash
make -C "$MAME_SOURCE_ROOT" -j2 SUBTARGET=neodiag \
  SOURCES=src/mame/skeleton/alphasneo.cpp
python3 devices/st7565/st7565test.py \
  --mame "$MAME_SOURCE_ROOT/neodiag" --rompath /absolute/path/to/private/roms \
  --output /tmp/st7565-run-001
```

The ROM directory must contain the `asneo` files expected by that build.
The firmware suite was qualified with the July 2013 Neo system ROM. It uses
native firmware LCD operations, not Betawise applets. The parallel-bus suite
checks device handlers, reset, RAM boundaries, command parameters, save states,
and rendering. The firmware suite checks exact pixel/raster results and
save/restore. Both run with disposable configuration/NVRAM. Commands and logs are retained in
the printed output directory (a new temporary directory unless `--output` is set). See
[the LCD notes](devices/st7565/README.md).

## Palm interrupt compatibility comparison

The optional before/after regression exercises other DragonBall machines to
check that the interrupt change does not alter their sampled behavior. Supply
both builds and private ROMs as described in
[the Palm instructions](devices/mc68328/palm/README.md), then run:

```bash
python3 devices/mc68328/palm/compare.py
```

It compares exact pixel buffers and CPU/interrupt traces; matching screens are
bounded compatibility evidence, not proof of full machine functionality.

## Contribution and artifact policy

Keep tests focused on MAME hardware/device behavior. Coordinate Betawise feature
coverage in its own repository. A new test should state the MAME revision,
required ROM identity (hash, not ROM bytes), command, expected result, and limits.
Use fresh/disposable RAM, flash, and configuration; never a user's saved session.
Neo validation must use deterministic local pixels/RAM, never model inference.
Do not generate expected images from a failing capture.

Keep local run logs, raw records, hashes, and assertion results outside Git; share
reviewable summaries and reproduction steps. Generated artifacts, private ROMs,
and executables are ignored. Review new fixtures for provenance and licensing.

## Licensing and provenance

This repository is licensed under BSD-3-Clause; see [LICENSE](LICENSE).
The initial copy came from the local MAME USB test
tree and external MAME validation directory, with path changes for standalone
use. No Betawise feature tests
are included. The original test files have been left in place.

Repository extraction and documentation were assisted by Codex (GPT-6).

## Import validation (2026-11-20)

Against MAME source `6a7b11dffbd`: interrupt fixture, D11 C++ suite, and both
USB/IP unittest cases passed. Python sources compile and all three Lua scripts
parse with MAME's bundled Lua. LCD and Palm firmware integration runs were not
repeated during extraction; their accompanying notes describe historical runs.
