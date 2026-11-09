# X99 G367H "Above 4G Decoding" unlock (no flash, no modded BIOS)

中文 | English

A hidden `Above 4G Decoding` setup question exists in the AMI Aptio V firmware
of the HSGM/Vulcan **X99-PF4 (board code G367H, GHX99014)** clone board, but it
is greyed out / invisible in the Setup menu. With a Tesla P40 / V100 (BAR1 =
16 GB) the board prints `OUT OF RESOURCES` at POST and refuses to assign the
64-bit MMIO window.

This repo contains the **zero-flash fix**: patch the NVRAM variable directly
from the UEFI Shell with `dmpstore`. No SPI flash, no CH341A, no modded BIOS,
fully reversible.

Result on our board (stock 5.11 BIOS, never reflashed for this fix):

```
04:00.0 3D controller: NVIDIA GV100GL [Tesla V100 SXM2 16GB]
    Region 1: Memory at 383800000000 (64-bit, prefetchable) [size=16G]
```

## How it works

IFRExtractor-RS over the stock firmware shows the question is real:

```
OneOf Prompt: "Above 4G Decoding", QuestionId: 0x3B,
              VarStore: "Setup", VarOffset: 0x3A, Size: 8, Min: 0x0, Max: 0x1
    OneOfOption "Disabled" Value: 0, Default, MfgDefault
    OneOfOption "Enabled"  Value: 1
```

- Variable: `Setup`, GUID `EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9` (AMI setup GUID),
  total size `0x72` bytes.
- Byte `0x3A` = 0 (factory default) is why the menu never shows it enabled; the
  menu item itself is additionally greyed out by a hidden `GrayOutIf` condition,
  which is why you cannot just toggle it in Setup.
- Setting `0x3A = 1` in NVRAM routes the IIO / `$PCIINITL` DXE modules through
  their native Above-4G code paths, and the root-bridge 64-bit window appears.
  (We proved earlier that poking NB fence registers or code-patching the size
  code does nothing while this flag byte is 0 — the flag is the master switch.)

## Files

```
stick/                 drop-in UEFI Shell payload (see USAGE.md)
  startup.nsh          auto-run: loads efidump/setup_a4g.bin, verifies
  rollback.nsh         restores efidump/setup_orig.bin (factory byte 0x3A=0)
  probe.nsh            optional diagnostics dump (vars/memmap/pci/smbios)
  efidump/
    setup_a4g.bin      dmpstore container: Setup var with 0x3A = 1
    setup_orig.bin     dmpstore container: Setup var exactly as dumped (0x3A = 0)
tools/
  build_setup_a4g.py   flip 0x3A=1 in YOUR OWN dumped Setup var (recommended path)
  verify_container.py  parse/verify any dmpstore -s container
docs/
  ifr-evidence.md      the IFR findings + variable layout
results/               before/after evidence (sanitized)
```

## ⚠️ Read before using

- `stick/efidump/*.bin` were captured from **our** board. The `Setup` var also
  stores fan curves, RTC wake times etc. — board-specific values. They work on
  the same G367H firmware, but the *safe* path for any board is:
  dump your own var, flip one byte with `tools/build_setup_a4g.py`, load that.
- Everything is reversible: `rollback.nsh`, or in the Shell manually:
  `dmpstore -all -l efidump\setup_orig.bin`
- If something goes wrong, a CMOS clear / NVRAM reset restores factory defaults.
- This changes NVRAM only. If you clear CMOS the patch is gone — re-run the stick,
  or bake the byte into the SPI `StdDefaults` region (advanced, not included).

## Quick start

See [USAGE.md](USAGE.md).

## License / disclaimer

Do it at your own risk; a wrong variable write can brick firmware settings
(CMOS clear recovers). Firmware belongs to the board vendor — this repo ships
no BIOS images, only variable containers and scripts.
