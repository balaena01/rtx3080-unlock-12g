@echo off
setlocal
cd /d "%~dp0"
if not exist build mkdir build
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\Llvm\x64\bin\clang.exe" -std=c11 -O1 -Wall -Wextra -Werror -Wno-unused-parameter -Wno-sign-compare -D_CRT_SECURE_NO_WARNINGS -D__KERNEL__ -DGU_TARGET_PCI_ID=0x220610deu -I tests/transaction_shim tests/test_transaction_3080.c vendor/prep_610.c vendor/layout_610.c vendor/vbios_610.c vendor/gfw_eval.c -o build/transaction-3080.exe
if errorlevel 1 exit /b 1
build\transaction-3080.exe "..\evidence\boot-03\PROM.BIN" "..\analysis\pinned-assets"
exit /b %errorlevel%
