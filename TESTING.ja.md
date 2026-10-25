# ビルドと検証

[English](TESTING.md) | **日本語** | [한국어](TESTING.ko.md)

## 基本検査

Windows で README のコンパイラと Python をインストールしたあと、リポジトリのルートで実行します。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\test-all.ps1
```

基本検査は probe、port／Bus Master、preflight、runtime、PE 拒否検査、USB パッケージツールを実行します。`evidence/boot-03/REPORT.TXT` を preflight の fixture として使います。GPU と UEFI サービスは模擬環境です。

Python のパッケージ検査だけを実行する場合:

```text
python -m unittest discover -s tools -p "test_*.py" -v
```

## ローカル fixture を使う追加検査

次のファイルを用意したうえで `-WithLocalFixtures` を指定します。

- `analysis/pinned-assets/`: `unlock/assets.json` のアセット 5 個。
- `evidence/boot-03/PROM.BIN`: 1MiB、SHA256 `F3DC8F07B0B8C9856D192DF172DFA7F7F84AC17EF6EDFDB448AD7FA94EFD2789`。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\test-all.ps1 -WithLocalFixtures
```

transaction、SHA256、EFI transaction、アプリ全体と FWSEC の順序比較の検査が追加されます。PROM fixture は記録済みのボードに対する回帰検査の入力です。別のカードのキャプチャに差し替えたものを同じ検証と解釈しないでください。

## ソースとパッケージのハッシュ

`SOURCE-MANIFEST.json` には公開ソースファイルの一覧と SHA256 が入っています。USB パッケージツールはこの一覧にあるファイルだけを `SOURCE.zip` に入れ、ビルド入力・EFI・実行用アセットを検査します。個人の作業ファイルやビルドキャッシュはパッケージに入れません。

ソースを変更した開発者は、新しいファイルを Git に追加し、ソース manifest を更新してから再度ビルド・検査します。

```powershell
git add .
python .\tools\source_manifest.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\unlock\test-all.ps1
```

`tools/source_manifest.py` は Git の追跡ファイルを基準に動作します。ZIP で受け取ったソースは、同梱の manifest を使ってそのままビルド・パッケージできます。

検査結果は `unlock/build/test-results.json` に記録します。host／mock での通過と、実際の USB 起動の結果は別物です。
