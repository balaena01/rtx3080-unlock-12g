#!/usr/bin/env bash
# Linux build of the read-only unlock preflight (EFI), with the same compiler
# and linker flags as unlock/build.ps1. Nothing here touches hardware: the
# preflight image only reads config space, the firmware BAR descriptor and the
# PROM window, then returns to firmware.
#   ./preflight-linux.sh [preflight|all|usb]
# Outputs land in unlock/build/<name>/ next to the Windows build tree.
#     preflight  MSI RTX 3080 12GB (10de:220a) + GU_PREFLIGHT
#     all        preflight, the 220a transaction build and the default 2206
#                transaction build (compile/verify only, never staged)
#     usb        stage the preflight image as build/usb-preflight/EFI/BOOT/BOOTX64.EFI
set -euo pipefail
cd "$(dirname "$0")/unlock"

CLANG=${CLANG:-clang}
LLD_LINK=${LLD_LINK:-lld-link}
PYTHON=${PYTHON:-python3}
EDK2=(-I ../deps/edk2/MdePkg/Include -I ../deps/edk2/MdePkg/Include/X64)
EFI_CFLAGS=(-target x86_64-pc-windows-msvc -std=c11 -ffreestanding -fno-builtin
            -fno-stack-protector -mno-red-zone -fshort-wchar -Os
            -Wall -Wextra -Werror -Wno-unused-parameter
            -D__KERNEL__ -DGU_UEFI_PORT -I compat)
SOURCES=(app app_io ownership format runtime sha256 checks port compat
         vendor/unlock_610 vendor/prep_610 vendor/layout_610 vendor/vbios_610
         vendor/gfw_eval)

# build_image <name> <extra cflags...>
build_image() {
  local name=$1; shift
  local objects=() source object
  mkdir -p "build/$name"
  for source in "${SOURCES[@]}"; do
    object="build/$name/${source//\//_}.obj"
    "$CLANG" "${EFI_CFLAGS[@]}" "${EDK2[@]}" "$@" -c "$source.c" -o "$object"
    objects+=("$object")
  done
  "$LLD_LINK" /nologo /nodefaultlib /subsystem:efi_application /entry:efi_main \
    /machine:x64 /base:0 /dynamicbase /nxcompat /timestamp:0 /opt:ref /opt:icf \
    "/map:build/$name/BOOTX64.map" "/out:build/$name/BOOTX64.EFI" "${objects[@]}"
  "$PYTHON" -I verify_pe.py "build/$name/BOOTX64.EFI" "build/$name/BOOTX64.map" \
    --output "build/$name/pe-verification.json" >/dev/null
  echo "verified build/$name/BOOTX64.EFI"
}

# 12GB card. GU_TARGET_PCI_ID feeds the vendor gates in unlock_610.c; the
# board profile in port.h owns identity, cold state and the VBIOS hash.
BOARD_220A=(-DGU_BOARD_220A -DGU_TARGET_PCI_ID=0x220a10deU)

build_preflight() {
  build_image preflight-12gb "${BOARD_220A[@]}" -DGU_PREFLIGHT
}

build_transaction_12gb() {
  build_image transaction-12gb "${BOARD_220A[@]}"
}

build_transaction_10gb() {
  build_image transaction-10gb -DGU_TARGET_PCI_ID=0x220610deU
}

stage_usb() {
  build_preflight
  install -d build/usb-preflight/EFI/BOOT
  install -m 0644 build/preflight-12gb/BOOTX64.EFI build/usb-preflight/EFI/BOOT/BOOTX64.EFI
  sha256sum build/usb-preflight/EFI/BOOT/BOOTX64.EFI
  echo "stage build/usb-preflight to the USB root; \\RTX3080-UNLOCK must already exist"
}

case "${1:-preflight}" in
  preflight) build_preflight ;;
  all) build_preflight; build_transaction_12gb; build_transaction_10gb ;;
  usb) stage_usb ;;
  *) echo "usage: $0 [preflight|all|usb]" >&2; exit 2 ;;
esac
