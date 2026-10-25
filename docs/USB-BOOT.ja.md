# USB の準備と起動

[English](USB-BOOT.md) | **日本語** | [한국어](USB-BOOT.ko.md)

この案内は README に記載した MSI RTX 3080 の実験環境を対象にしています。既存の実行は確認済みですが、新しく用意した FAT32 USB へ移した構成での実起動はまだ検証していません。

## 準備

- x64 UEFI 環境、Secure Boot を無効化、画面は Intel 内蔵グラフィックスに接続。
- 空の FAT32 USB。フォーマットが必要な場合は、USB 内の既存ファイルを先にバックアップし、書き込み先のデバイスを確認します。
- ビルドした `BOOTX64.EFI`、または配布されている USB テンプレート。
- `unlock/assets.json` と名前・サイズ・SHA256 が一致するアセット 5 個。アセットの準備方法は[上流プロジェクトの firmware ドキュメント](https://github.com/Zagitta/gpu-unlock/tree/0ebdb1c6308b6a2072be5bf04513472942541956/firmware)を参照してください。

Windows のデバイス暗号化／BitLocker を使っている PC では、ファームウェア設定を変更する前に回復キーを確認しておいてください。

## ローカルでパッケージを作る

リポジトリのルートで実行します。先に EFI をビルドし、そのあとアセット 5 個をローカルの `assets` ディレクトリに用意します。下のコマンドは新しいローカルフォルダを作るだけで、USB をフォーマットしたり自動で選択したりはしません。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
python .\tools\package_usb.py --assets .\assets --output .\usb-package
```

`--assets` を省略すると、実行用アセットを除いたテンプレートが作られます。テンプレート内の `ASSETS/REQUIRED-ASSETS.json` は必要なファイルの一覧であってアセット本体ではないので、5 個のファイルは別途用意する必要があります。

完成した `usb-package` **の中身**を USB の最上位にコピーします。`usb-package` フォルダ自体を 1 階層下に入れないでください。

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

`RTX3080-UNLOCK` フォルダはログを書ける必要があります。`BOOTX64.EFI` だけをコピーした状態では実行できません。このアプリはファイル内容とボード条件を再び検査します。

## 実行

1. Windows の作業を保存して PC を完全に終了し、電源を入れます。ドライバがすでに使った warm 状態の GPU では、検査が拒否されることがあります。
2. マザーボードの起動メニューで **UEFI USB** を選びます。検証した ASUS ボードでは F8 を使いました。
3. `READY` まで事前検査が終わったら、**U を一度**押します。Esc、または U を押さずに 30 秒の待機が過ぎるとキャンセルです。
4. 実行中は USB を抜いたり再起動したりしないでください。
5. `UEFI transaction completed and cleaned up` が表示されてファームウェアに戻ったら、**Windows Boot Manager** を選びます。途中で再起動すると適用状態が維持されない可能性があります。

USB アプリが再び開いたら Esc で抜けてください。同じ起動で U をもう一度押さないでください。

`STOP / POWER OFF` が表示されたら、電源ボタンで PC を切ります。その画面から Windows へ進まないでください。再試行する前に `RTX3080-UNLOCK/RUNxx/REPORT.TXT` を確認します。

## 適用範囲

UEFI での成功は、Windows での性能向上や長時間の安定性を保証しません。まずデバイスの状態を確認し、自分の作業で性能を比較してください。次のコールドブートのあとも効果が残るかは確認していません。

既存の Windows ディスクのブートローダーを変える必要はありません。USB を使うのをやめるときは USB を外し、Windows Boot Manager で起動します。
