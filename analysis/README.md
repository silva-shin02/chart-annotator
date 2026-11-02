# 分析用スクリプト（アプリ本体ではない）

アプリの「⚙ 設定 → バックアップ → 📊 分析用に書き出す」で作った JSON（`chart-annotator-analysis_YYYYMMDD.json`）を入力に、
手元（クラウドセッションの作業フォルダ）で集計して Artifact（Web ページ）にするためのもの。JSON は個人データなのでリポジトリに入れない。

## 逆張り空売りの手法探索（本命・2026-11-02）
```
python3 -I analysis/prep.py   <書き出しJSON> work/days3.pkl     # 日ごとの1分足（EMAは前日から連続で計算し直す）
python3 -I analysis/os3.py    work/days3.pkl work/os3.json      # 8/20以降・前場・ティックVAP で全ライン×条件を総当たり
# os3.json を analysis/ に置いてから:
python3 -I analysis/make_report.py <出力html>                    # os3tpl.html にデータを埋め込んでページを作る
```
- `os3.py` のルール（すべてユーザーと選択肢で決めた前提）は CLAUDE.md §11 を参照。
- `make_report.py` は自分と同じフォルダの `os3.json` と `os3tpl.html` を読む。

## その他（前段の試作）
- `os_events.py` + `tpl.html`：寄り足ラインの「割る→戻って上抜ける」場面の挙動統計（寄り足ライン OS検証ページ）。
- `snload.js`（SN 本体の計算関数を node の vm で読み込む。`SN_DIR` で scalping-notebook の場所を指定）+ `snrecs.js` + `ctx.py` + `sntpl.html`：
  SN の記録（8/20以降）に CA の足データから状況を付けて比べるページ（SNエントリー 状況別成績）。
