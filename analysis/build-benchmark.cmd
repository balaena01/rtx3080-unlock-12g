@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin\nvcc.exe" -std=c++17 -O3 -arch=sm_86 -Xcompiler /utf-8 compute-benchmark.cu -lcublas -o compute-benchmark.exe
exit /b %errorlevel%
