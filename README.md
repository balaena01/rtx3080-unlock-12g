# RTX 3080 Unlock

MSI RTX 3080 10GB에서 검증한 Windows용 UEFI 연산 언락 실험입니다. USB로 UEFI 앱을 실행한 뒤, 재부팅 없이 Windows로 이어서 부팅합니다.

**지원 범위는 아래의 실험 환경입니다.** 다른 제조사의 RTX 3080이나 RTX 3090을 지원하는 범용 도구가 아닙니다. 장치·화면 경로·펌웨어 검사에 맞지 않으면 실행을 거부합니다.

## USB로 사용하기

1. [USB 준비 및 부팅 안내](docs/USB-BOOT.md)에 따라 FAT32 USB와 필요한 파일을 준비합니다.
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

## 빌드와 검사

Windows 개발 환경: LLVM/clang 12 + lld-link(VS2019 BuildTools), MSVC 환경(VS2022 Community), Python 3.9 이상. 스크립트의 기본 도구 경로는 이 설치 구성을 기준으로 합니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\test-all.ps1
```

빌드는 `unlock/build/BOOTX64.EFI`를 만들고 PE 형식을 검사합니다. 검사 명령은 GPU를 실행하지 않습니다. 추가 fixture를 사용하는 전체 모의 검사와 패키지 생성 방법은 [TESTING.md](TESTING.md)를 참고하세요.

## 출처와 라이선스

이 프로젝트의 포트와 재사용 코어는 **GPL-2.0-only**입니다. 핵심 코드는 [Zagitta/gpu-unlock](https://github.com/Zagitta/gpu-unlock/tree/0ebdb1c6308b6a2072be5bf04513472942541956)에서 가져왔습니다. 포함된 EDK2 헤더와 관련 고지는 각각의 라이선스를 따릅니다.

[LICENSE](LICENSE)와 [외부 코드 고지](THIRD_PARTY_NOTICES.md)를 확인하세요.
