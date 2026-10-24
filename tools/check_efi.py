"""Inspect a built UEFI application: format, self-containment and code.

Checks the PE32+ image itself rather than trusting linker flags, the COFF
objects it was linked from, the linker map and a disassembly (binutils
objdump). Exit status is nonzero on any failure.
"""
import argparse
import re
import struct
import subprocess
import sys
from pathlib import Path

DIRS = ["export", "import", "resource", "exception", "security", "basereloc",
        "debug", "architecture", "globalptr", "tls", "load_config",
        "bound_import", "iat", "delay_import", "clr", "reserved"]
# Data directories a freestanding UEFI application has no use for.
MUST_BE_EMPTY = ["export", "import", "security", "globalptr", "tls",
                 "load_config", "bound_import", "iat", "delay_import", "clr"]
# AMD64 COFF relocations that become absolute addresses in the image.
ABSOLUTE_RELOCS = {1: "ADDR64", 2: "ADDR32"}
# Instructions that would reach an OS or hardware without UEFI services.
# int3 is excluded: the linker pads between functions with it.
FORBIDDEN = re.compile(r"\t(syscall|sysenter|sysexit|sysret|int|into|in|out|ins[bwd]?|"
                       r"outs[bwd]?|rdmsr|wrmsr|hlt|cli|sti|lgdt|lidt|ltr|invd|wbinvd)\b"
                       r"|\tmov\s+cr\d|\tmov\s+\w+,cr\d")

problems = []


def need(cond, msg):
    print(("OK   " if cond else "FAIL ") + msg)
    if not cond:
        problems.append(msg)


def check_objects(paths):
    """Return the number of absolute relocations across the COFF objects."""
    absolute = 0
    for path in paths:
        obj = Path(path).read_bytes()
        machine, nsec = struct.unpack_from("<HH", obj, 0)
        need(machine == 0x8664, f"{Path(path).name}: AMD64 COFF object")
        optsize = struct.unpack_from("<H", obj, 16)[0]
        kinds = {}
        for i in range(nsec):
            at = 20 + optsize + 40 * i
            relptr, = struct.unpack_from("<I", obj, at + 24)
            nrel, = struct.unpack_from("<H", obj, at + 32)
            for j in range(nrel):
                kind, = struct.unpack_from("<H", obj, relptr + 10 * j + 8)
                kinds[kind] = kinds.get(kind, 0) + 1
                absolute += kind in ABSOLUTE_RELOCS
        print(f"     {Path(path).name}: relocation types {kinds}")
    return absolute


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("efi")
    p.add_argument("--map", required=True, help="lld-link /map output")
    p.add_argument("--objects", nargs="+", required=True, help="objects given to the linker")
    p.add_argument("--objdump", default="objdump")
    a = p.parse_args()

    data = Path(a.efi).read_bytes()
    u16 = lambda o: struct.unpack_from("<H", data, o)[0]
    u32 = lambda o: struct.unpack_from("<I", data, o)[0]

    print("[format]")
    need(data[:2] == b"MZ", "DOS signature MZ")
    pe = u32(0x3C)
    need(data[pe:pe + 4] == b"PE\0\0", "PE signature")
    machine, nsec, _, _, _, optsize, chars = struct.unpack_from("<HHIIIHH", data, pe + 4)
    need(machine == 0x8664, f"machine AMD64 (0x{machine:04x})")
    need(chars & 0x0002 and not chars & 0x2000, f"executable image, not a DLL (0x{chars:04x})")
    opt = pe + 24
    need(u16(opt) == 0x20B, "optional header PE32+")
    entry = u32(opt + 16)
    base = struct.unpack_from("<Q", data, opt + 24)[0]
    salign, falign, size_image = u32(opt + 32), u32(opt + 36), u32(opt + 56)
    need(u16(opt + 68) == 10, f"subsystem EFI_APPLICATION ({u16(opt + 68)})")
    print(f"     image base 0x{base:x}, section align 0x{salign:x}, file align 0x{falign:x}, "
          f"SizeOfImage 0x{size_image:x}, DllCharacteristics 0x{u16(opt + 70):04x}")
    need(salign % 0x1000 == 0 and salign >= falign, "page-multiple section alignment")
    nrva = u32(opt + 108)
    need(nrva >= 16, f"data directories present ({nrva})")
    dirs = {DIRS[i]: struct.unpack_from("<II", data, opt + 112 + 8 * i) for i in range(min(nrva, 16))}

    sections = []
    for i in range(nsec):
        at = opt + optsize + 40 * i
        name = data[at:at + 8].rstrip(b"\0").decode(errors="replace")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, at + 8)
        sch = u32(at + 36)
        sections.append((name, vaddr, vsize, rawptr, rawsize, sch))
        flags = "".join(f if sch & bit else "-" for f, bit in
                        (("R", 0x40000000), ("W", 0x80000000), ("X", 0x20000000)))
        print(f"     section {name:<8} rva=0x{vaddr:05x} vsize=0x{vsize:05x} {flags}")
        need(rawptr + rawsize <= len(data) and vaddr % salign == 0 and vaddr + vsize <= size_image,
             f"section {name} aligned and inside file and image")
        need(not (sch & 0x80000000 and sch & 0x20000000), f"section {name} not writable and executable")
    text = [s for s in sections if s[5] & 0x20000000]
    need(any(s[1] <= entry < s[1] + s[2] for s in text), f"entry RVA 0x{entry:x} in executable code")

    print("[self-contained]")
    for name in MUST_BE_EMPTY:
        need(dirs.get(name, (0, 0)) == (0, 0), f"no {name} directory")
    m = Path(a.map).read_text()
    found = re.search(r"^\s*[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+efi_main\s+([0-9A-Fa-f]+)", m, re.M)
    need(bool(found) and int(found[1], 16) == base + entry, "entry point is efi_main in the map")
    linked = set(re.findall(r"^\s*[0-9A-Fa-f]{4}:[0-9A-Fa-f]{8}\s+\S+\s+[0-9A-Fa-f]{16}\s+(?:\S+:)?(\S+)$", m, re.M))
    expected = {Path(o).name for o in a.objects}
    print(f"     symbols come from: {sorted(linked)}")
    need(linked <= expected and not re.search(r"\.lib\b", m, re.I), "only the given objects, no libraries")
    absolute = check_objects(a.objects)
    reloc_rva, reloc_size = dirs.get("basereloc", (0, 0))
    if absolute:
        need(reloc_size > 0, f"{absolute} absolute relocations are covered by a .reloc table")
    else:
        print(f"     no absolute addresses in the objects; .reloc size {reloc_size} is not required")

    print("[code]")
    dis = subprocess.run([a.objdump, "-d", "-M", "intel", "--no-show-raw-insn", a.efi],
                         capture_output=True, text=True, check=True).stdout
    insns = [l for l in dis.splitlines() if re.match(r"^\s+[0-9a-f]+:\t", l)]
    print(f"     {len(insns)} instructions")
    bad = [l.strip() for l in insns if FORBIDDEN.search(l)]
    need(not bad, "no syscall/int/port I/O/MSR/control-register/hlt/cli instructions"
         + (f": {bad[:5]}" if bad else ""))
    lo = min(s[1] for s in text) + base
    hi = max(s[1] + s[2] for s in text) + base
    direct = [int(t, 16) for t in re.findall(r"\tcall\s+(?:0x)?([0-9a-f]+)(?:\s|$)", dis, re.M)]
    need(bool(direct), "direct calls were found (the disassembly was parsed)")
    need(all(lo <= t < hi for t in direct), f"all {len(direct)} direct calls stay inside the image")
    indirect = len(re.findall(r"\tcall\s+(?:QWORD PTR \[|r\w+$)", dis, re.M))
    print(f"     {indirect} indirect calls (UEFI services and protocols reached through tables)")

    print("RESULT:", "PASS" if not problems else f"FAIL ({len(problems)})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
