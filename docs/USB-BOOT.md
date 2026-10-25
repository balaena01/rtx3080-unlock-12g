# USB preparation and booting

**English** | [日本語](USB-BOOT.ja.md) | [한국어](USB-BOOT.ko.md)

This guide targets the MSI RTX 3080 experimental environment stated in the README. Existing runs are confirmed, but booting from a freshly prepared FAT32 USB stick has not been validated yet.

## Preparation

- An x64 UEFI environment, Secure Boot disabled, and the display connected to the Intel integrated graphics.
- An empty FAT32 USB stick. If it needs formatting, back up the files already on the stick first and confirm which device you are about to write.
- The built `BOOTX64.EFI`, or the provided USB template.
- The five assets whose names, sizes and SHA256 values match `unlock/assets.json`. For how to prepare the assets, see the [firmware documentation of the upstream project](https://github.com/Zagitta/gpu-unlock/tree/0ebdb1c6308b6a2072be5bf04513472942541956/firmware).

On a PC that uses Windows device encryption / BitLocker, check your recovery key before changing firmware settings.

## Building the package locally

Run this from the repository root. Build the EFI first, then place the five assets in a local `assets` directory. The commands below create a new local folder; they do not format a USB stick and do not select one automatically.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
python .\tools\package_usb.py --assets .\assets --output .\usb-package
```

If you omit `--assets`, the template is produced without the runtime assets. `ASSETS/REQUIRED-ASSETS.json` inside the template is the list of required files, not the assets themselves, so the five files must be prepared separately.

Copy the **contents** of the finished `usb-package` to the root of the USB stick. Do not nest the `usb-package` folder one level down.

```text
USB:/
  EFI/BOOT/BOOTX64.EFI
  RTX3080-UNLOCK/
    ASSETS/
      booter_load_ga102.bin
      v67-ga102-610.43.03.bin
      gsp_ga10x.bin
      gsp_boot_ga102.bin
      gsp_boot_desc_ga102.bin
    LICENSES/
    SOURCE.zip
  USB-README.md
  PACKAGE.json
  SHA256SUMS.txt
```

The `RTX3080-UNLOCK` folder must be writable so the application can record logs. Copying only `BOOTX64.EFI` is not enough to run: the application re-checks the file contents and the board conditions.

## Running

1. Save your Windows work, power the PC off completely, then power it on. If the GPU is in a warm state left over from the driver, the checks may refuse to run.
2. In the motherboard boot menu, select the **UEFI USB** entry. F8 was used on the validated ASUS board.
3. Once the pre-checks finish and `READY` is shown, press **U once**. Esc, or waiting out the 30-second timeout without pressing U, cancels.
4. Do not unplug the USB stick or reboot while the run is in progress.
5. When `UEFI transaction completed and cleaned up` appears and control returns to the firmware, select **Windows Boot Manager**. Rebooting in between may not keep the applied state.

If the USB application opens again, leave it with Esc. Do not press U a second time in the same boot.

If `STOP / POWER OFF` appears, turn the PC off with the power button. Do not continue into Windows from that screen. Inspect `RTX3080-UNLOCK/RUNxx/REPORT.TXT` before trying again.

## Scope

A successful UEFI run does not guarantee better performance in Windows or long-run stability. Check the device state first and compare performance in your own workload. Whether the effect survives the next cold boot has not been confirmed.

You do not need to change the bootloader of your existing Windows disk. To stop using the USB route, remove the stick and boot Windows Boot Manager as usual.
