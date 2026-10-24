"""check_efi.py must reject damaged copies of a good image, not just pass it."""
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

tool = Path(__file__).with_name("check_efi.py")
efi, map_path, *objects = sys.argv[1:]
original = Path(efi).read_bytes()
pe = struct.unpack_from("<I", original, 0x3C)[0]
opt = pe + 24


def run(image):
    return subprocess.run([sys.executable, "-I", str(tool), str(image), "--map", map_path,
                           "--objects", *objects], capture_output=True, text=True)


def padding_to_hlt(data):
    """Replace one int3 padding byte (after a ret) with hlt."""
    at = data.find(b"\xc3\xcc")
    assert at > 0, "no ret/int3 padding to mutate"
    data[at + 1] = 0xF4


mutations = [
    ("machine", lambda d: d.__setitem__(slice(pe + 4, pe + 6), b"\0\0")),
    ("subsystem", lambda d: d.__setitem__(slice(opt + 68, opt + 70), b"\x03\0")),
    ("import directory", lambda d: d.__setitem__(slice(opt + 120, opt + 124), b"\x00\x30\0\0")),
    ("hlt instruction", padding_to_hlt),
]
assert run(efi).returncode == 0, "the unmodified image must pass"
failures = 0
with tempfile.TemporaryDirectory(prefix="check-efi-") as scratch:
    for name, mutate in mutations:
        data = bytearray(original)
        mutate(data)
        path = Path(scratch) / "mutated.efi"
        path.write_bytes(data)
        rejected = run(path).returncode != 0
        print(f"{'PASS' if rejected else 'FAIL'} checker rejects a damaged {name}")
        failures += not rejected
print(f"Checker self-test: {'PASS' if not failures else 'FAIL'}")
sys.exit(1 if failures else 0)
