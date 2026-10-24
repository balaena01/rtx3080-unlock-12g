#pragma once
#include <Uefi.h>
#include <Protocol/PciIo.h>
#include <IndustryStandard/Acpi10.h>

/* LEVEL-R769-127-VBX: MSI RTX 3080 12GB (GA102, 10de:220a, subsystem 1462:3896). */
#define PROBE_TARGET_ID 0x220a10deU
#define PROBE_TARGET_SUBSYSTEM 0x38961462U
#define PROBE_SAMPLE_COUNT 46
#define PROBE_PROM_OFFSET 0x00300000ULL
#define PROBE_PROM_SIZE 0x00100000U
#define PROBE_ROM_LIMIT 0x01000000U

typedef struct {
  UINT32 Offset;
  UINT32 Value;
  EFI_STATUS Status;
} PROBE_SAMPLE;

typedef struct {
  UINT32 Config[64];
  UINT64 BarSize;
  EFI_STATUS BarStatus;
  BOOLEAN MemoryEnabled;
  PROBE_SAMPLE Samples[PROBE_SAMPLE_COUNT];
} PROBE_RESULT;

BOOLEAN ProbeMatches(const UINT32 *Config);
EFI_STATUS ProbeCollect(EFI_PCI_IO_PROTOCOL *Pci, EFI_BOOT_SERVICES *Bs,
                       PROBE_RESULT *Result);
EFI_STATUS ProbeReadProm(EFI_PCI_IO_PROTOCOL *Pci, const PROBE_RESULT *Result,
                        VOID *Buffer, UINTN Size);
BOOLEAN ProbeRomUsable(const VOID *Buffer, UINT64 Size);
