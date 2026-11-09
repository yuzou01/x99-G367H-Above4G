#!/usr/bin/env python3
"""Bake "Above 4G Decoding" (Setup var byte 0x3A = 1) into a G367H 16 MB SPI image.

Locates the AMI NVRAM FFS (GUID cef5b9a3-...) in both NVRAM banks, walks the
NVAR entries, and flips byte 0x3A in EVERY copy of the "Setup" variable
(0x72-byte data): the live entries AND the copies nested inside StdDefaults,
so the setting survives a CMOS clear too. AMI NVAR entries carry no per-entry
checksum, so a same-length in-place byte flip is safe.

Works on the stock dump, on modded builds (r7-r11 era), and on a fresh
`flashrom -E` read of the chip — offsets are found dynamically.

Usage:
    python3 bake_a4g_into_spi.py stock_or_dump.bin patched.bin

Then flash with e.g.:
    flashrom -p ch341a_spi -w patched.bin
"""
import re
import struct
import sys
import uuid

FFS2 = bytes.fromhex("78e58c8c3d8a1c4f9935896185c32dd3")  # AMI FFS2 GUID
NVRAM_FFS_PREFIX = "cef5b9a3"
NAME_RE = re.compile(rb"([A-Za-z][A-Za-z0-9_]{2,40})\x00")
OFF_ABOVE4G = 0x3A
SETUP_DATA_LEN = 0x72


def find_ffs(d, prefix):
    out = []
    for m in re.finditer(rb"_FVH", d):
        hdr = m.start() - 0x28
        if hdr < 0 or d[hdr + 0x10:hdr + 0x20] != FFS2:
            continue
        fvlen = int.from_bytes(d[hdr + 0x20:hdr + 0x28], "little")
        hlen = int.from_bytes(d[hdr + 0x30:hdr + 0x32], "little")
        ext = int.from_bytes(d[hdr + 0x34:hdr + 0x36], "little")
        end = hdr + fvlen
        if end > len(d):
            continue
        off = (hdr + max(hlen, (ext + 0x14) if ext else 0) + 7) // 8 * 8
        while off + 0x18 <= end:
            if d[off:off + 8] == b"\xff" * 8:
                break
            typ = d[off + 18]
            size = d[off + 20] | (d[off + 21] << 8) | (d[off + 22] << 16)
            if not (0x18 <= size < 0x800000) or typ not in set(range(1, 0x14)) | {0xF0}:
                break
            g = str(uuid.UUID(bytes_le=bytes(d[off:off + 16])))
            if g.startswith(prefix):
                out.append((off, size))
            off += (size + 7) // 8 * 8
    return out


def nvar_entries(buf, base=0):
    out = []
    for m in re.finditer(b"NVAR", buf):
        off = m.start()
        if off + 12 > len(buf):
            continue
        dsz = struct.unpack_from("<H", buf, off + 4)[0]
        if not (12 <= dsz <= 0x20000):
            continue
        nm = NAME_RE.search(buf, off + 8)
        if not nm or nm.start() > off + 40:
            continue
        name = nm.group(1).decode()
        doff = nm.end()
        end = min(off + dsz, len(buf))
        out.append((base + off, name, base + doff, buf[doff:end]))
    return out


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    d = bytearray(open(argv[1], "rb").read())
    if len(d) != 0x1000000:
        print("ERROR: expected a 16 MB full SPI dump")
        return 1

    banks = find_ffs(d, NVRAM_FFS_PREFIX)
    if not banks:
        print("ERROR: NVRAM FFS not found — is this a G367H/G367-family dump?")
        return 1
    print(f"NVRAM banks: {[hex(o) for o, _ in banks]}")

    targets = set()
    for ffs_off, ffs_size in banks:
        ffs = d[ffs_off:ffs_off + ffs_size]
        for eoff, name, doff, data in nvar_entries(ffs, base=ffs_off):
            if name == "Setup" and len(data) >= OFF_ABOVE4G + 1:
                targets.add(doff + OFF_ABOVE4G)
            if name == "StdDefaults":
                for e2, n2, d2, data2 in nvar_entries(ffs[doff - ffs_off:doff - ffs_off + len(data)], base=doff):
                    if n2 == "Setup" and len(data2) >= OFF_ABOVE4G + 1:
                        targets.add(d2 + OFF_ABOVE4G)
    if not targets:
        print("ERROR: no Setup variable entries found")
        return 1

    for off in sorted(targets):
        if d[off - OFF_ABOVE4G - 6:off - OFF_ABOVE4G] != b"Setup\x00":
            print(f"ERROR: sanity check failed at {hex(off)}")
            return 1
        print(f"{hex(off)}: {d[off]:#x} -> 0x1")
        d[off] = 1
    open(argv[2], "wb").write(d)
    print(f"wrote {argv[2]} ({len(targets)} copies patched)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
