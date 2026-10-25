# RTX 3080 Unlock

[English](README.md) | [日本語](README.ja.md) | **한국어**

MSI RTX 3080 10GB에서 검증한 Windows용 UEFI 연산 언락 실험입니다. USB로 UEFI 앱을 실행한 뒤, 재부팅 없이 Windows로 이어서 부팅합니다.

**지원 범위는 아래의 실험 환경입니다.** 다른 제조사의 RTX 3080이나 RTX 3090을 지원하는 범용 도구가 아닙니다. 장치·화면 경로·펌웨어 검사에 맞지 않으면 실행을 거부합니다.

## USB로 사용하기

1. [USB 준비 및 부팅 안내](docs/USB-BOOT.ko.md)에 따라 FAT32 USB와 필요한 파일을 준비합니다.
2. UEFI 부팅 메뉴에서 USB를 선택합니다.
3. 사전 검사가 끝나 `READY`가 표시되면 **U를 한 번** 누릅니다.
4. 성공 후 펌웨어 메뉴로 돌아오면 **Windows Boot Manager**를 선택합니다. 이 사이에 재부팅하지 않습니다.

USB 템플릿에는 EFI, 소스, 사용법과 라이선스가 들어 있습니다. 실행 자산 5개는 로컬에서 추가해야 합니다. `unlock/assets.json`에 파일명·크기·SHA256이 정리되어 있습니다. 템플릿만 복사한 상태에서는 실행할 수 없습니다.

## 확인한 환경

- MSI RTX 3080 10GB: PCI `10de:2206`, subsystem `1462:3890`, VBIOS `94.02.59.00.aa`.
- ASUS TUF GAMING B660M-PLUS D4, Intel i5-13600K / UHD 770 화면 출력.
- Windows 11 Pro build 26200, NVIDIA 610.60 드라이버.
- v0.10 실제 실행: UEFI transaction과 정리 완료 후 Windows CUDA 측정.

현재 코드는 BDF `0000:01:00.0`, BAR, 보드 PROM 및 Intel 화면 경로도 검사합니다. 같은 제품명이어도 다른 PC에서의 동작은 확인되지 않았습니다. 새 FAT32 USB에서의 실제 부팅은 별도 검증 대상입니다.

## 측정 결과

| 측정 | 이전 TFLOPS | 적용 후 TFLOPS | 변화 |
| --- | ---: | ---: | ---: |
| FP32 pedantic | 22.057145 | 21.922047 | −0.61% |
| FP16 Tensor / FP32 누산 | 60.874030 | 109.217226 | +79.42% |
| BF16 Tensor / FP32 누산 | 60.910719 | 113.090926 | +85.67% |

동일 실행 파일과 CUDA/cuBLAS 환경의 4096×4096 GEMM 측정입니다. 기준값은 한 프로세스, 적용 후 값은 세 프로세스 중앙값들의 중앙값입니다. 게임 성능, 모든 AI 작업의 향상률, 장시간 안정성이나 콜드부팅 후 지속성을 의미하지 않습니다. [측정 자료](results/benchmark.json)와 [실제 UEFI 실행 로그](evidence/unlock-boot-09/REPORT.TXT)를 함께 제공합니다. 측정 자료에서는 개인 경로와 장치 UUID를 제외했습니다.

## PyTorch 계측 (matmul, FP32 누산)

| 종류 | 해제 전 | 해제 후 | 증가 | SM 클럭 (전 → 후) |
| --- | ---: | ---: | ---: | --- |
| BF16 4096 | 58.6 | 101.0 | +72% | 1815 → 1530 MHz |
| FP16 4096 | 57.4 | 97.7 | +70% | 1800 → 1485 MHz |
| BF16 8192 | 61.4 | 112.7 | +84% | 1905 → 1643 MHz |
| FP16 8192 | 60.5 | 109.6 | +81% | 1875 → 1605 MHz |
| TF32 4096 | 28.3 | 51.1 | +80% | 1905 → 1635 MHz |
| FP32 4096 (비교용) | 17.8 | 19.1 | +7% | 1515 → 1485 MHz |

단위는 TFLOPS. PyTorch matmul(FP32 누산)을 같은 카드, 같은 하네스로 측정했습니다. 해제 전 열은
해제 전에 이 카드에서 별도 세션으로 얻은 값입니다. 원본 값은 [results/pytorch-matrix.json](results/pytorch-matrix.json)에 있습니다.

SM 클럭으로 나눠 보면 무슨 일이 일어났는지가 보입니다.

- BF16·FP16·TF32는 해제 후 **클럭당 ×2.0~2.1**(32.3 → 66.0, 31.9 → 65.8, 32.3 → 68.6,
  32.3 → 68.3, 14.9 → 31.3 TFLOPS/GHz)입니다. 텐서 경로가 모두 2배가 되었고, 이는 반속
  텐서 경로가 되살아났을 때의 모양 그대로입니다.
- 실측 증가가 70~84%에 그치는 것은 해제 후 실행이 더 낮은 클럭에 자리잡기 때문입니다
  (1815 → 1530 MHz 등). 클럭당 처리량은 2배가 되고 그 일부를 클럭이 되돌려 준 셈입니다.
  클럭이 내려가는 이유 자체는 직접 측정하지 않았고, 소비전력 예산이 유력합니다.
- FP32 4096은 클럭당 ×1.09입니다. FP32는 패치 대상 경로를 쓰지 않으므로 해제 효과가 아니라
  클럭과 측정 편차로 읽어야 합니다. 위의 cuBLAS `fp32_pedantic`(−0.61%)과도 어긋나지만
  이는 다른 하네스입니다.

## llama.cpp prefill (Saluki 27B IQ2)

| 프롬프트 길이 | prefill 전 | prefill 후 | 증가 | 생성 |
| --- | ---: | ---: | ---: | --- |
| 512 토큰 | 849 tok/s | 945 tok/s | +11% | 변화 없음 |
| 2048 토큰 | 959 tok/s | 1042 tok/s | +9% | 변화 없음 |
| 8192 토큰 | 1006 tok/s | 1086 tok/s | +8% | 변화 없음 |

`llama-server`(llama.cpp), Saluki 27B IQ2의 prefill 처리량. 해제 전후 같은 카드.
데이터는 [results/llm-prefill.json](results/llm-prefill.json)에 있습니다.

- 증가는 1할 정도이고 2배가 되지는 않습니다. IQ2 모델은 계산의 대부분을 양자화 커널로
  돌리며, 그 경로는 패치 대상인 FP16 텐서 경로를 지나지 않습니다. 늘어난 것은 attention의
  일부처럼 FP16으로 도는 부분입니다.
- 생성 속도는 움직이지 않습니다. 토큰을 하나씩 내보내는 추론은 메모리 대역으로 정해지고,
  해제는 VRAM 대역을 바꾸지 않기 때문입니다. 예상대로입니다.
- 커널 단위 프로파일은 뜨지 않았으므로 위 구분은 숫자에서 읽은 추론이며 계측이 아닙니다.

## 빌드와 검사

Windows 개발 환경: LLVM/clang 12 + lld-link(VS2019 BuildTools), MSVC 환경(VS2022 Community), Python 3.9 이상. 스크립트의 기본 도구 경로는 이 설치 구성을 기준으로 합니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\test-all.ps1
```

빌드는 `unlock/build/BOOTX64.EFI`를 만들고 PE 형식을 검사합니다. 검사 명령은 GPU를 실행하지 않습니다. 추가 fixture를 사용하는 전체 모의 검사와 패키지 생성 방법은 [TESTING.ko.md](TESTING.ko.md)를 참고하세요.

## 12GB(220a) 프로필과 리드온리 preflight

`unlock/port.h`는 보드 프로필을 컴파일 시점에 고릅니다. 기본값은 위에서 검증한 10GB
(`10de:2206` / `1462:3890`)이고, `-DGU_BOARD_220A`를 주면 12GB
(`10de:220a` / `1462:3896`, 12288MiB, PROM SHA256 `799d147b…`)가 됩니다. 두 프로필의
기대값은 각 카드의 펌웨어 덤프에서만 가져왔으므로 섞어 쓰면 안 됩니다.

```bash
./preflight-linux.sh preflight     # build/preflight-12gb/BOOTX64.EFI
./preflight-linux.sh transaction   # build/transaction-12gb/BOOTX64.EFI
./preflight-linux.sh all           # 위 둘 + 검증된 10GB transaction
./preflight-linux.sh usb           # build/usb-preflight/EFI/BOOT/BOOTX64.EFI
```

`preflight` 빌드는 `-DGU_PREFLIGHT`로 ARM/transaction 코드를 링크에서 제외합니다.
config space, 펌웨어 BAR 기술자, PROM 창 MMIO를 읽기만 하고 GPU에는 아무것도 쓰지
않으며, PciIo 독점 열기도 검사 직후 닫습니다. 실패하면 어느 게이트에서 멈췄는지가
콘솔과 `REPORT.TXT`에 남습니다. 12GB 실기의 게이트 기대값, 오프라인 재평가 도구
(`analysis/r769/preflight_gate_replay.py`), 실행 절차는 워크스페이스의
`analysis/r769/preflight-12gb.md`에 정리되어 있습니다.

12GB 프로필의 실기 상태: 읽기 전용 preflight는 10개 게이트 모두 PASS, 본 transaction은
1회 실행해 `status=0 stage=transaction attempted=1 driver_release=1 clean=1`(`FLR=1`)로
완료했습니다. 그 실행 후 FP16 Tensor GEMM은 109.5 TFLOPS이고, 해제 전에 같은 카드에서
별도 세션으로 받은 60.5~61.4 TFLOPS와 짝을 이룹니다. 다만 번갈아 다시 측정한 것은 아니므로
비율은 참고값으로 읽어 주세요. 패치는 해당 부팅의 VRAM에만 있고 재부팅하면 사라집니다.

## 출처와 라이선스

이 프로젝트의 포트와 재사용 코어는 **GPL-2.0-only**입니다. 핵심 코드는 [Zagitta/gpu-unlock](https://github.com/Zagitta/gpu-unlock/tree/0ebdb1c6308b6a2072be5bf04513472942541956)에서 가져왔습니다. 포함된 EDK2 헤더와 관련 고지는 각각의 라이선스를 따릅니다.

[LICENSE](LICENSE)와 [외부 코드 고지](THIRD_PARTY_NOTICES.md)를 확인하세요.
