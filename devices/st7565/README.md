# External ST7565R validation

These scripts are validation artifacts for the Neo LCD device PR. They are
outside the MAME repository. They test MAME hardware behavior, not Betawise features.
No ROM images are included.

From the MAME repository directory, after building `neodiag`, run:

```sh
python3 /path/to/mame-alphasmart-tests/devices/st7565/st7565test.py --mame ./neodiag --rompath /path/to/roms
```

The ROM directory must contain user-supplied `asneo` ROMs. Validation used the
July 2013 Neo system ROM. The runner creates temporary configuration and NVRAM
directories, runs the debugger-backed parallel-bus suite (64 checks), and then
runs the firmware pixel/raster suite. It fails on a missing success marker,
reported test failure, nonzero MAME exit status, or timeout.

The parallel-bus suite covers real MAME device bus handlers, debugger reads,
state saving, hardware/software reset, RAM bounds, command parameters, and
rendering modes. The firmware suite covers all 264 x 64 pixels, both controller
boundaries, repeated screen save/restore, drawing/capture, and all seven raster
operations.
