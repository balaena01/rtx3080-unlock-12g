#pragma once
#include <Uefi.h>
#include <Protocol/PciIo.h>
#include <Protocol/DevicePath.h>
#include <stddef.h>

/* Board profile. Defaults describe the validated MSI RTX 3080 10GB
   (10de:2206 / 1462:3890). -DGU_BOARD_220A selects the MSI RTX 3080 12GB
   (10de:220a / 1462:3896); never mix the two, every expected value below is
   taken from one card's own firmware dump. */
#if defined(GU_BOARD_220A)
#define GU_BOARD_ID 0x220a10deU
#define GU_BOARD_SUBSYSTEM 0x38961462U
#define GU_BOARD_LABEL "MSI RTX 3080 12GB"
/* Live BAR0+0x300000, byte-identical over three consecutive probe boots. */
#define GU_BOARD_PROM_SHA256 \
  "799d147bfc7ef2c094668b5197c0425eb6692c6b623435a2803b15f9aee80a97"
/* 12288 MiB, read back from FEAT 0x001183a4. */
#define GU_BOARD_FB_MB 0x3000U
/* SS0 (0x0082381c) is boot-unstable: 0x01521103, 0x01521013 and 0x01521003
   were observed over three boots. Only the bits common to all three are a
   gate, so a re-boot cannot reject the card for a volatile bit. */
#define GU_BOARD_SS0_MASK 0x01521003U
#define GU_BOARD_SS0_VALUE 0x01521003U
/* SS1 (0x00823820) was 5 in every probe boot; the 10GB profile accepts 2 or 3. */
#define GU_BOARD_SS1_BITS 0x00000020U
#else
#define GU_BOARD_ID 0x220610deU
#define GU_BOARD_SUBSYSTEM 0x38901462U
#define GU_BOARD_LABEL "MSI RTX 3080 10GB"
#define GU_BOARD_PROM_SHA256 \
  "f3dc8f07b0b8c9856d192df172dfa7f7f84ac17ef6edfdb448ad7fa94efd2789"
#define GU_BOARD_FB_MB 0x2800U
#define GU_BOARD_SS0_MASK 0xffffffffU
#define GU_BOARD_SS0_VALUE 0x46254040U
#define GU_BOARD_SS1_BITS 0x0000000cU
#endif
/* GA102 die ID at BAR0+0; 0xb72000a1 in every probe boot of both cards. */

#define GU_BOARD_CHIP 0xb72000a1U
typedef struct GU_DMA GU_DMA;
struct GU_DMA {
  GU_DMA *next;
  VOID *cpu, *mapping;
  UINT64 dma;
  UINTN bytes, pages;
  BOOLEAN mapped;
};
typedef struct {
  EFI_BOOT_SERVICES *bs;
  EFI_PCI_IO_PROTOCOL *pci;
  EFI_HANDLE image, handle;
  UINT64 bar_base, bar_size, ticks;
  UINT16 pm_cap, pcie_cap, msi_cap, msix_cap;
  UINT32 saved_config[64];
  UINT16 saved_devctl, saved_devctl2;
  UINT8 pcie_version;
  BOOLEAN fault, retained, started, quiesced, armed, owned, display_ok, saved;
  BOOLEAN master_attributes_pending;
  UINT64 master_original_attributes;
  UINT16 master_original_command;
  EFI_PCI_IO_PROTOCOL *master_pci;
  /* Containment may run at TPL_NOTIFY. Capture diagnostics without file IO;
     preserve first errors even if a later containment retry succeeds. */
  EFI_STATUS master_attribute_status, master_hardware_status;
  UINT64 master_last_attributes;
  UINT16 master_last_command;
  UINT32 flrs, mmio_writes, dma_count;
  GU_DMA *allocations;
  BOOLEAN (*display_check)(VOID);
} GU_PLATFORM;
extern GU_PLATFORM Gu;

VOID GuInit(EFI_BOOT_SERVICES *Bs, EFI_PCI_IO_PROTOCOL *Pci);
BOOLEAN GuTargetConfig(const UINT32 *Config, UINTN Segment, UINTN Bus, UINTN Device, UINTN Function);
BOOLEAN GuSafeToReturn(VOID);
EFI_STATUS GuDmaAllocate(UINTN Bytes, VOID **Cpu, UINT64 *Dma);
EFI_STATUS GuDmaFree(VOID *Cpu, UINT64 Dma);
UINT32 GuRead32(UINT32 Offset);
VOID GuWrite32(UINT32 Offset, UINT32 Value);
EFI_STATUS GuSavePci(VOID);
EFI_STATUS GuRestorePci(VOID);
EFI_STATUS GuFlr(VOID);
EFI_STATUS GuClearMaster(VOID);
EFI_STATUS GuEnableMaster(VOID);
EFI_STATUS GuConfigRead(EFI_PCI_IO_PROTOCOL_WIDTH Width, UINT32 Offset, VOID *Value);
EFI_STATUS GuConfigWrite(EFI_PCI_IO_PROTOCOL_WIDTH Width, UINT32 Offset, VOID *Value);
VOID GuStarted(VOID);
VOID GuQuiesced(VOID);
VOID GuLog(const char *Format, ...);
VOID GuLogText(const char *Text);
VOID GuCopyFromIo(VOID *Destination, const VOID *Source, size_t Bytes);
VOID *GuAlloc(size_t Bytes);
VOID GuFree(VOID *Memory);
VOID GuStall(UINTN Microseconds);
