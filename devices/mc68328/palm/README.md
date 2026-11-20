# External DragonBall compatibility smoke test

The MAME interrupt change was compared against its parent implementation using
the same combined `asma3k`/Palm build. Only `mc68328.cpp` was replaced for the
baseline build, then the fixed source and normal binary were restored.
No test instrumentation was added to MAME source.

## Firmware

Images are publicly accessible at https://palmdb.net/app/palm-roms-complete .
These are third-party firmware downloads, not entries in MAME's officially
licensed free-ROM collection. ROMs are local test inputs and are not committed
or redistributed with the change. The historical private provenance record documented preparation and hashes.
Expected ROM SHA-1 values for reproduction are:

- `palmiii`, Palm OS 3.3 English, MC68328:
  SHA1 `e4626f1d33eca8368284d906b2152dcd28b71bbd`.
  The downloaded image omits its zero-filled tail; pad to 2 MiB.
- `palmiiic`, Palm OS 4.0 English, MC68EZ328:
  SHA1 `54321dcaedcc80de57a819cfd599d8d1b2e26eeb`.
- `palmm100`, Palm OS 3.5.1 English, MC68EZ328:
  SHA1 `c46248d6f05cb2f4337985610cedfbdc12ac47cf`.

## Executed coverage and results

Each binary ran each machine from fresh state for 1200 screen frames. Normal
input events pressed/released the pen at (80,80), Button 1 and Power twice.
Nine checkpoints per machine captured raw screen pixels, PNGs, PC, SR, IMR,
ISR and IPR. No guest firmware, registers or RAM were patched by the replay.
All 27 screen checkpoints were byte-identical between before and after; all
three sampled CPU/interrupt traces were identical. All six runs exited normally.
The external interrupt fixture separately fails with the pre-fix methods and
passes with the fixed methods.

This is bounded before/after compatibility coverage, not proof of complete
Palm functionality, successful navigation through every first-boot prompt,
or comprehensive wake/sleep correctness. In particular some later m100
captures are blank in both versions; matching blank frames are not counted
as proof of successful wake. Earlier nonblank screens are preserved as well.
No model/vision inference was used: pixel buffers and trace bytes were compared
directly. A full MAME build and DEBUG=1 build have not been run for this change.

## Reproduction

Historical run logs, binaries, provenance files, and captures were not imported
into this repository. Supply builds named `mame-before` and `mame-after` beside
`compare.py`, each containing the three Palm drivers above. Put your own ROMs
under `roms/<machine>/` beside the script, with MAME's expected filenames. Record
both build commits and firmware hashes alongside your results.

Run `python3 devices/mc68328/palm/compare.py` from the repository root. It creates
`runs/` beside the script and refuses to overwrite an existing run directory.
Move previous results aside before rerunning. Logs, commands, raw pixel buffers,
PNGs and traces are retained there, and `comparison.json` records the results.
The runner fails on missing/different checkpoints, trace mismatch, nonzero exit,
or timeout. These generated files and local binaries/ROMs are ignored by Git.

The sibling firmware-free fixture runs with:

```bash
MAME_SOURCE_ROOT=/path/to/mame python3 -m unittest discover \
  -s devices/mc68328 -p test_mc68328_interrupts.py -v
```
