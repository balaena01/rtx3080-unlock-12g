# RTX 3080 Unlock

[English](README.md) | **日本語** | [한국어](README.ko.md)

MSI RTX 3080 10GB で検証した、Windows 向け UEFI 計算アンロック実験です。USB から UEFI アプリを実行し、そのあと再起動せずに Windows へ続けて起動します。

**サポート範囲は下記の実験環境だけです。** 他社製 RTX 3080 や RTX 3090 に対応する汎用ツールではありません。デバイス・画面経路・ファームウェア検査が一致しない場合、実行を拒否します。

## USB から使う

1. [USB の準備と起動の案内](docs/USB-BOOT.md)（現在は韓国語）に従って、FAT32 の USB と必要なファイルを用意します。
2. UEFI の起動メニューで USB を選びます。
3. 事前検査が終わって `READY` が表示されたら、**U を一度**押します。
4. 成功後ファームウェアのメニューに戻るので、**Windows Boot Manager** を選びます。その間に再起動はしません。

USB テンプレートには EFI、ソース、使い方、ライセンスが入っています。実行用アセット 5 個はローカルで追加する必要があります。ファイル名・サイズ・SHA256 は `unlock/assets.json` にまとまっています。テンプレートだけをコピーした状態では実行できません。

## 確認した環境

- MSI RTX 3080 10GB: PCI `10de:2206`、subsystem `1462:3890`、VBIOS `94.02.59.00.aa`。
- ASUS TUF GAMING B660M-PLUS D4、Intel i5-13600K / UHD 770 で画面出力。
- Windows 11 Pro build 26200、NVIDIA 610.60 ドライバ。
- v0.10 の実実行: UEFI トランザクションと後片付けが完了し、その後 Windows 側で CUDA 計測。

現在のコードは BDF `0000:01:00.0`、BAR、ボード PROM、Intel の画面経路も検査します。同じ製品名でも他の PC での動作は確認していません。新しい FAT32 USB での実起動は別途の検証対象です。

## 計測結果

| 計測 | 適用前 TFLOPS | 適用後 TFLOPS | 変化 |
| --- | ---: | ---: | ---: |
| FP32 pedantic | 22.057145 | 21.922047 | −0.61% |
| FP16 Tensor / FP32 累算 | 60.874030 | 109.217226 | +79.42% |
| BF16 Tensor / FP32 累算 | 60.910719 | 113.090926 | +85.67% |

同じ実行ファイルと同じ CUDA/cuBLAS 環境での 4096×4096 GEMM 計測です。基準値は 1 プロセス、適用後の値は 3 プロセスの中央値の中央値です。ゲーム性能、あらゆる AI 作業の向上率、長時間の安定性、コールドブート後の持続性を意味するものではありません。[計測資料](results/benchmark.json)と[実際の UEFI 実行ログ](evidence/unlock-boot-09/REPORT.TXT)を併せて公開しています。計測資料からは個人パスとデバイス UUID を除いてあります。

## ビルドと検査

Windows 開発環境: LLVM/clang 12 + lld-link（VS2019 BuildTools）、MSVC 環境（VS2022 Community）、Python 3.9 以上。スクリプトの既定ツールパスはこの構成を前提にしています。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\test-all.ps1
```

ビルドは `unlock/build/BOOTX64.EFI` を作り、PE 形式を検査します。検査コマンドは GPU を実行しません。追加 fixture を使う完全な模擬検査とパッケージ作成の方法は [TESTING.md](TESTING.md)（現在は韓国語）を参照してください。

## 12GB（220a）プロファイルと読み取り専用 preflight

`unlock/port.h` はボードプロファイルをコンパイル時に選びます。既定は上で検証した 10GB（`10de:2206` / `1462:3890`）で、`-DGU_BOARD_220A` を付けると 12GB（`10de:220a` / `1462:3896`、12288 MiB、PROM SHA256 `799d147b…`）になります。両プロファイルの期待値はそれぞれのカードのファームウェアダンプからのみ取っているので、混ぜて使ってはいけません。

```bash
./preflight-linux.sh preflight     # build/preflight-12gb/BOOTX64.EFI
./preflight-linux.sh transaction   # build/transaction-12gb/BOOTX64.EFI
./preflight-linux.sh all           # 上記 2 つ + 検証済みの 10GB transaction
./preflight-linux.sh usb           # build/usb-preflight/EFI/BOOT/BOOTX64.EFI
```

`preflight` ビルドは `-DGU_PREFLIGHT` を渡し、ARM/transaction のコードをリンクから外します。config space、ファームウェアの BAR 記述子、PROM ウィンドウの MMIO を読むだけで GPU には何も書かず、PciIo の排他オープンも検査直後に閉じます。失敗した場合はどのゲートで止まったかがコンソールと `REPORT.TXT` に残ります。12GB 実機のゲート期待値、オフライン再評価ツール（`analysis/r769/preflight_gate_replay.py`）、実行手順はワークスペースの `analysis/r769/preflight-12gb.md` にまとまっています。

12GB プロファイルの実機状況: 読み取り専用 preflight は 10 ゲートすべて PASS、本番トランザクションは 1 回実行して `status=0 stage=transaction attempted=1 driver_release=1 clean=1`（`FLR=1`）で完了しました。その実行後の FP16 Tensor GEMM は 109.5 TFLOPS です。同じ 12GB 機での pre-unlock 計測はまだ取っていません。パッチはその起動の VRAM 上だけにあり、再起動で消えます。

## 出典とライセンス

このプロジェクトの移植部分と再利用コアは **GPL-2.0-only** です。中核コードは [Zagitta/gpu-unlock](https://github.com/Zagitta/gpu-unlock/tree/0ebdb1c6308b6a2072be5bf04513472942541956) から取得しています。同梱の EDK2 ヘッダと関連する告知は、それぞれのライセンスに従います。

[LICENSE](LICENSE) と[外部コードの告知](THIRD_PARTY_NOTICES.md)を確認してください。
