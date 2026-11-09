# Usage

## What you need

- A FAT32-formatted USB stick (any size).
- A UEFI Shell on it. Easiest: download the prebuilt edk2 Shell
  (https://github.com/pbatard/UEFI-Shell/releases), install it to the stick,
  which gives you `EFI/BOOT/BOOTX64.EFI` that boots straight into the Shell.
- Copy this repo's `stick/` contents to the **root** of the stick
  (`startup.nsh` and `efidump/` end up at `FS0:\startup.nsh`, `FS0:\efidump\`).

## Path A — recommended: patch YOUR OWN Setup var

Works on any AMI Aptio V board that has the question (check with
`docs/ifr-evidence.md` how to confirm).

1. Boot the stick into the UEFI Shell.
2. Dump your Setup variable:

   ```
   Shell> dmpstore Setup -guid EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9 -s setup_mine.bin
   ```

   If that says "No matching variables found", list everything and find your
   setup store name/GUID:

   ```
   Shell> dmpstore -all | grep -i setup
   ```

3. Copy `setup_mine.bin` off the stick to a PC and flip the byte:

   ```
   python3 tools/build_setup_a4g.py setup_mine.bin setup_a4g.bin
   ```

4. Put the result back on the stick as `efidump\setup_a4g.bin`, reboot into the
   Shell — `startup.nsh` loads it automatically and re-dumps it for verification
   (`verify_setup.bin` must be the same size as your dump, CRC OK).
5. Power off, pull the stick, boot normally. Check:

   ```
   sudo lspci -vvv -s <GPU> | grep -A2 "Region 1"
   ```

## Path B — quick test with our prebuilt container (G367H only)

1. Copy `stick/*` to the stick root as described above.
2. Boot the stick on the target board. The Shell auto-runs `startup.nsh`:

   ```
   ==== [1/3] load setup_a4g.bin ====
   ==== [2/3] verify: re-save Setup var ====
   FS0:\efidump\verify_setup.bin  ... 158 bytes
   ```

3. If the verify file is 158 B: power off, pull the stick, boot normally.
4. Rollback any time: boot the stick and run

   ```
   Shell> fs0:
   Shell> rollback.nsh
   ```

## Scripting rules learned (if you write your own .nsh)

This AMI Shell build is picky:

- Files must use **CRLF** line endings.
- No `rem` comments (use nothing, or `echo`), no single-line `if`.
- Quote every `echo` string (a bare `-` becomes "Unknown flag").
- First line `fs0:` and use absolute `FS0:\...` paths everywhere.
- `dmpstore -l` **without** `-all`/`-guid` silently matches only the EFI Global
  GUID and loads nothing. Always use `dmpstore -all -l file.bin`.
- `dmpstore NAME -s file` without `-guid` writes a 0-byte file.
- The Shell's own `>` redirection can fail on some AMI builds; prefer tools
  that open files themselves (`dmpstore -s`, `dmpstore -l`).
