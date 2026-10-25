# RTX 3080 Unlock

**English** | [日本語](README.ja.md) | [한국어](README.ko.md)

A UEFI compute-unlock experiment for Windows, validated on an MSI RTX 3080 10GB. A UEFI application runs from a USB stick and then hands control straight back to Windows Boot Manager, without a reboot in between.

**The supported scope is only the experimental environment listed below.** This is not a general-purpose tool for RTX 3080 cards from other vendors, nor for the RTX 3090. If the device, the display path or the firmware checks do not match, the application refuses to run.

## Running it from USB

1. Prepare a FAT32 USB stick and the required files as described in [USB preparation and booting](docs/USB-BOOT.md).
2. Select the USB stick in the UEFI boot menu.
3. When the read-only checks finish and `READY` is shown, press **U once**.
4. After success, control returns to the firmware menu: choose **Windows Boot Manager**. Do not reboot in between.

The USB template contains the EFI application, the sources, usage notes and licenses. The five runtime assets must be added locally; `unlock/assets.json` lists their file names, sizes and SHA256 values. A template copied as-is cannot run.

## Tested environment

- MSI RTX 3080 10GB: PCI `10de:2206`, subsystem `1462:3890`, VBIOS `94.02.59.00.aa`.
- ASUS TUF GAMING B660M-PLUS D4, Intel i5-13600K / UHD 770 for display output.
- Windows 11 Pro build 26200, NVIDIA 610.60 driver.
- v0.10 real run: UEFI transaction and cleanup completed, then CUDA measurements on the Windows side.

The current code also checks BDF `0000:01:00.0`, BARs, the board PROM and the Intel display path. The same product name on a different PC has not been validated. Booting from a freshly built FAT32 USB stick is still a separate validation item.

## Measured results

| Measurement | Before (TFLOPS) | After (TFLOPS) | Change |
| --- | ---: | ---: | ---: |
| FP32 pedantic | 22.057145 | 21.922047 | −0.61% |
| FP16 Tensor / FP32 accumulate | 60.874030 | 109.217226 | +79.42% |
| BF16 Tensor / FP32 accumulate | 60.910719 | 113.090926 | +85.67% |

These are 4096×4096 GEMM measurements taken with the same executable and the same CUDA/cuBLAS environment. The baseline is a single process; the post-unlock value is the median of three process medians. They do not imply game performance, the speedup of every AI workload, long-run stability, or persistence across a cold boot. [Measurement data](results/benchmark.json) and the [real UEFI run log](evidence/unlock-boot-09/REPORT.TXT) are included. Personal paths and device UUIDs were removed from the measurement data.

## Build and test

Windows development environment: LLVM/clang 12 + lld-link (VS2019 BuildTools), an MSVC environment (VS2022 Community), Python 3.9 or newer. The default tool paths in the scripts assume this installation.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\test-all.ps1
```

The build produces `unlock/build/BOOTX64.EFI` and checks the PE format. The test commands do not touch the GPU. For the full simulated test that needs extra fixtures, and for packaging, see [TESTING.md](TESTING.md).

## 12GB (220a) profile and the read-only preflight

`unlock/port.h` selects the board profile at compile time. The default is the 10GB card validated above (`10de:2206` / `1462:3890`); `-DGU_BOARD_220A` selects the 12GB card (`10de:220a` / `1462:3896`, 12288 MiB, PROM SHA256 `799d147b…`). Every expected value in both profiles comes from that card's own firmware dump, so the two must never be mixed.

```bash
./preflight-linux.sh preflight     # build/preflight-12gb/BOOTX64.EFI
./preflight-linux.sh transaction   # build/transaction-12gb/BOOTX64.EFI
./preflight-linux.sh all           # both of the above + the validated 10GB transaction
./preflight-linux.sh usb           # build/usb-preflight/EFI/BOOT/BOOTX64.EFI
```

The `preflight` build passes `-DGU_PREFLIGHT` and drops the ARM/transaction code at link time. It only reads config space, firmware BAR descriptors and the PROM window over MMIO, writes nothing to the GPU, and closes the exclusive PciIo open as soon as each check is done. On failure, the gate that stopped it is printed on the console and recorded in `REPORT.TXT`. Gate expectations for the 12GB card, the offline replay tool (`analysis/r769/preflight_gate_replay.py`) and the run procedure are documented in `analysis/r769/preflight-12gb.md` in the workspace.

Hardware status of the 12GB profile: the read-only preflight passes all ten gates, and one transaction run completed with `status=0 stage=transaction attempted=1 driver_release=1 clean=1` (`FLR=1`). FP16 Tensor GEMM measured 109.5 TFLOPS after that run. A pre-unlock measurement on the same 12GB machine has not been taken yet; the patch lives only in VRAM for the current boot and is gone after a reboot.

## Provenance and license

The port and the reused core of this project are **GPL-2.0-only**. The core code comes from [Zagitta/gpu-unlock](https://github.com/Zagitta/gpu-unlock/tree/0ebdb1c6308b6a2072be5bf04513472942541956). The bundled EDK2 headers and related notices keep their own licenses.

See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md).
