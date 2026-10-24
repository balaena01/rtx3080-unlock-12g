#!/usr/bin/env bash
# Linux build of the read-only probe (EFI + host tests), with the same compiler
# and linker flags as unlock/build.ps1. Needs clang, lld-link and objdump.
#   ./build-linux.sh [all|test|probe]
set -euo pipefail
cd "$(dirname "$0")"

CLANG=${CLANG:-clang}
LLD_LINK=${LLD_LINK:-lld-link}
PYTHON=${PYTHON:-python3}
EDK2=(-I deps/edk2/MdePkg/Include -I deps/edk2/MdePkg/Include/X64)
EFI_CFLAGS=(-target x86_64-pc-windows-msvc -std=c11 -ffreestanding -fno-builtin
            -fno-stack-protector -mno-red-zone -fshort-wchar -Os
            -Wall -Wextra -Werror -Wno-unused-parameter)
mkdir -p build

# Mocked PCI/MMIO/file system; never touches hardware. CHAR16 literals need
# a 16-bit wchar_t on Linux, as on Windows.
test_probe() {
  "$CLANG" -std=c11 -fshort-wchar -Wall -Wextra -Werror "${EDK2[@]}" \
    test_core.c probe_core.c probe_app.c -o build/test_core
  build/test_core
}

build_probe() {
  local objects=() source
  for source in probe_app probe_core efi_runtime; do
    "$CLANG" "${EFI_CFLAGS[@]}" "${EDK2[@]}" -c "$source.c" -o "build/probe_$source.obj"
    objects+=("build/probe_$source.obj")
  done
  "$LLD_LINK" /nologo /nodefaultlib /subsystem:efi_application /entry:efi_main \
    /machine:x64 /base:0 /dynamicbase /nxcompat /timestamp:0 /opt:ref /opt:icf \
    /map:build/PROBE.map /out:build/PROBE-BOOTX64.EFI "${objects[@]}"
  "$PYTHON" -I tools/check_efi.py build/PROBE-BOOTX64.EFI \
    --map build/PROBE.map --objects "${objects[@]}"
  "$PYTHON" -I tools/test_check_efi.py build/PROBE-BOOTX64.EFI build/PROBE.map "${objects[@]}"
  sha256sum build/PROBE-BOOTX64.EFI
}

case "${1:-all}" in
  test) test_probe ;;
  probe) build_probe ;;
  all) test_probe; build_probe ;;
  *) echo "usage: $0 [all|test|probe]" >&2; exit 2 ;;
esac
