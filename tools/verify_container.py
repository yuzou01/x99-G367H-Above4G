#!/usr/bin/env python3
"""Parse a dmpstore -s container: show name/GUID/attrs/CRC and the Above4G byte."""
import struct
import sys
import zlib


def main(path):
    d = open(path, "rb").read()
    nb, dl = struct.unpack_from("<II", d, 0)
    p = 8
    name = d[p:p + nb].decode("utf-16-le", "replace").rstrip("\x00"); p += nb
    guid = d[p:p + 16].hex(); p += 16
    attrs = struct.unpack_from("<I", d, p)[0]; p += 4
    data = d[p:p + dl]; p += dl
    crc = struct.unpack_from("<I", d, p)[0]
    ok = (zlib.crc32(d[:p]) & 0xFFFFFFFF) == crc
    print(f"file  : {path} ({len(d)} B)")
    print(f"var   : {name}  guid={guid}  attrs={attrs:#x}  datalen={dl:#x}")
    print(f"crc32 : {'OK' if ok else 'BAD!'}")
    if dl > 0x3A:
        print(f"0x3A (Above 4G Decoding) = {data[0x3A]:#x}")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
