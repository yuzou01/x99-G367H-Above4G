# IFR evidence & variable layout

## Where the knob lives

Extracted with [IFRExtractor-RS](https://github.com/LongSoft/IFRExtractor-RS)
via the [SetupVarGUIPlus](https://github.com/aryan-nikzad/SetupVarGUIPlus)
pipeline against the stock 16 MB SPI dump of the G367H:

```
Setup__body.bin.0.0.en-US.uefi.ifr.txt:
  OneOf Prompt: "Above 4G Decoding",
      Help: "Enables or Disables 64bit capable Devices to be Decoded in
             Above 4G Address Space (Only if System Supports 64 bit PCI Decoding)."
      QuestionId: 0x3B, VarStoreId: 0x1, VarOffset: 0x3A,
      Size: 8, Min: 0x0, Max: 0x1
    OneOfOption "Disabled" Value: 0, Default, MfgDefault
    OneOfOption "Enabled"  Value: 1
```

The question is wrapped in `GrayOutIf (EqIdVal QuestionId: 0x9A, Value: 0x1)`
and Q0x9A is a hidden `Numeric` question in a different VarStore
(`VarStoreId: 0x4`, offset 0x0) — that is why the option never appears
editable in the Setup menu even though the firmware fully implements it.

## Variable identity

| field | value |
|---|---|
| variable name | `Setup` |
| GUID | `EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9` |
| attributes | `NV+BS` (0x3) |
| data size | `0x72` |
| Above 4G byte | offset `0x3A`, 0 = Disabled (factory), 1 = Enabled |

Note the same GUID also stores `IntelSetup` (0x17CB, the big GRANTLEY
IIO/Platform setup blob) — do not confuse the two variables.

## dmpstore container format (`dmpstore -s`)

```
u32  nameBytes          (UTF-16 name length incl. NUL)
u32  dataLen
name (UTF-16LE + NUL)
GUID (16 B, mixed-endian as EFI stores it)
u32  attributes
data (dataLen bytes)
u32  CRC32 (zlib) over every preceding byte of this entry
```

`tools/verify_container.py` parses and checks it;
`tools/build_setup_a4g.py` flips one byte and recomputes the CRC.

## Related Platform knobs (IntelSetup var, same GUID, size 0x17CB)

For reference — these were **not** needed once `Setup:0x3A=1`:

```
MMIO Low Base    IntelSetup 0x10CE (u32)
MMIO Low Size    IntelSetup 0x10D2 (u32)
MMIOHBase        IntelSetup 0x10D6 (u32, "MMIOH Base [63:32]; must be between 4032-4078")
MMIO High Size   IntelSetup 0x10DA (u32: 0=256G default, 1=128G, 2=512G, 3=1024G)
```

Live values on our board were all zero (i.e. "use refcode defaults"), and the
default 256G MMIOH aperture is already far bigger than a 16 GB BAR — the
window size was never the bottleneck, the flag was.

## What we tried before (all failed, kept for reference)

- Forcing NB MMIOH fence/limit/base registers in the IioInit DXE module
  (3 code patches, reflashed via CH341A): POST fine, `OUT OF RESOURCES` unchanged.
- Forcing the IIO MMIOH *size code* argument (`push imm` variants): identical
  behaviour — the consumer has a special path gated on the Above4G flag being
  OFF that ignores the pushed size entirely.
- Donor bytes from other clone-brand firmwares (`IntelSetup` 0x2d4/0x2d6):
  loaded fine, no effect.
- Conclusion from disassembly: while `Setup:0x3A == 0`, every above-4G consumer
  short-circuits. One NVRAM byte beats all of the above.
