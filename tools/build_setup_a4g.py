#!/usr/bin/env python3
"""Flip "Above 4G Decoding" (Setup var offset 0x3A) to 1 in a dmpstore container.

Usage:
  1. Boot the UEFI Shell on the target board and dump YOUR OWN Setup var:

       dmpstore Setup -guid EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9 -s setup_mine.bin

     (the GUID is the AMI setup GUID; on G367H both "Setup" and "IntelSetup"
      share it. If your board differs, find it with:  dmpstore -l | grep -i setup )

  2. Run this tool:

       python3 build_setup_a4g.py setup_mine.bin setup_a4g.bin

  3. Put setup_a4g.bin into efidump/ on the stick and boot startup.nsh.

Container format written by `dmpstore -s` (single variable):
  [u32 nameBytes][u32 dataLen][name UTF-16LE + NUL][GUID 16B LE-mixed]
  [u32 attributes][data][u32 CRC32 (zlib) over everything before it]

This tool only flips byte 0x3A and recomputes the CRC. Everything else —
your fan curves, boot order, RTC wake, etc. — is preserved exactly.
"""
import struct
import sys
import zlib

OFF_ABOVE4G = 0x3A


def parse_one(blob: bytes):
    off = 0
    nb, dl = struct.unpack_from("<II", blob, off)
    off += 8
    if not (2 <= nb <= 256 and 8 <= dl <= 0x100000):
        raise ValueError(f"bad header nb={nb} dl={dl}")
    name = blob[off:off + nb].decode("utf-16-le", "replace").rstrip("\x00")
    off += nb
    guid = blob[off:off + 16]
    off += 16
    attrs = struct.unpack_from("<I", blob, off)[0]
    off += 4
    data = blob[off:off + dl]
    off += dl
    if len(data) != dl:
        raise ValueError("truncated data")
    crc = struct.unpack_from("<I", blob, off)[0]
    off += 4
    body = blob[:off - 4]
    if zlib.crc32(body) & 0xFFFFFFFF != crc:
        raise ValueError("CRC mismatch - is this a dmpstore -s file?")
    return name, guid, attrs, data, body


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = argv[1], argv[2]
    blob = open(src, "rb").read()
    name, guid, attrs, data, body = parse_one(blob)
    print(f"var      : {name}")
    g = guid.hex()
    print(f"guid     : {g[6:8]}{g[4:6]}{g[2:4]}{g[0:2]}-{g[10:12]}{g[8:10]}-"
          f"{g[14:16]}{g[12:14]}-{g[16:20]}-{g[20:32]}")
    print(f"attrs    : {attrs:#x}   datalen: {len(data):#x}")
    if len(data) <= OFF_ABOVE4G:
        print(f"ERROR: var too small to contain offset {OFF_ABOVE4G:#x}")
        return 1
    before = data[OFF_ABOVE4G]
    print(f"0x3A     : {before:#x} -> 0x1")
    if before == 1:
        print("already enabled, writing a copy anyway")
    new = bytearray(data)
    new[OFF_ABOVE4G] = 1
    # body = header + old data (CRC excluded). Rebuild: header + new data + new CRC
    header = body[:len(body) - len(data)]
    out = header + bytes(new)
    out += struct.pack("<I", zlib.crc32(out) & 0xFFFFFFFF)
    open(dst, "wb").write(out)
    print(f"wrote {dst} ({len(out)} B)")
    # self-verify
    n2, _, _, d2, _ = parse_one(out)
    assert n2 == name and d2[OFF_ABOVE4G] == 1
    print("re-parse OK, CRC OK, 0x3A = 0x1")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
