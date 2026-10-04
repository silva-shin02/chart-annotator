# チャート分析ツール (Chart Annotator) — 編集ガイド / 引継ぎテンプレ

> このファイルは次セッションが自動で読み込みます。**まず最初にこの「今回のタスク」を埋めてから依頼してください。**

---

## ✍️ 今回のタスク（ユーザー記入欄）

- **やりたいこと**：（例：◯◯ボタンを追加 / △△の挙動を変える / □□のバグを直す）
- **対象の機能/画面**：（例：スタンプ機能 / カレンダー検索 / チャート描画）
- **再現手順や具体例**（バグの場合）：
- **スクショ/データ**（あれば添付）：

---

## 0. 最重要ルール（このプロジェクト固有）

1. **編集対象は `index.html` 1ファイルのみ**（巨大・約12,900行・React UMD を1つの IIFE 内に全部入れた構成）。
2. **push のタイミング**：1つの依頼の修正がすべて終わってから、**まとめて1回 commit & push**（こまめに push しない）。
   - リポジトリ：`https://github.com/silva-shin02/chart-annotator`(branch: `main`)
   - **クラウドセッションで作業ブランチが指定されている場合**：そのブランチに push → PR 作成 → **毎回そのままマージ**（2026-09-30 ユーザー明示「毎回マージして」）。マージ済みブランチは次の依頼で `origin/main` から作り直す。
   - コミット末尾に `Co-Authored-By: Claude ...` を付ける。
3. **動作確認はユーザーが実機で行う**（Claudeは詳細な機能検証をしない）。← 2026-06-29 ユーザー明示ルール
   - 許容（任意・最小限）：`new Function(scriptText)` での**構文チェック**程度まで（自前CORSサーバ+preview_eval等）。起動・コンソールエラー確認も可。
   - **やらない**：preview_eval 等で **UI を操作する機能検証**（クリック手順の再現・タブ/モーダル操作・スクショでの動作確認）、**合成データの IDB/localStorage 注入**。これらは時間がかかり、ユーザーが実機で確認する方針。
   - 実装が終わったら commit & push し、ユーザーへは「**ハードリロード（Ctrl+Shift+R）して試して**」と伝えるだけにする（単一HTML＝ブラウザが強くキャッシュする）。
4. **ストレージはオリジン別**（参考）：ユーザー実環境は `file://`（null origin）、検証用 localhost は**別ストレージ**で実データ無し。※機能検証はユーザーが行うため合成データ注入は原則不要。

---

5. **頼まれた範囲だけ変える**（2026-10-04 の教訓）。曖昧な依頼を広く解釈して、頼まれていない部分（足・線など）まで変えない。
   - 例：「縦線より右の**帯**が暗く見えるのを直して」→ 帯だけ直す。足ごと消すのは NG だった（取り消し済み）。
   - 解釈が割れそうなら、**実装前に「〜という意味で合ってる？」と一文で確認**する（AskUserQuestion の選択肢 UI は閉じられがちなので、普通の文章で聞く）。
   - 「元に戻して」と言われたら、指定された時点と `git diff` で**完全一致**することを確かめてから push。

---

## 1. これは何か

日本株スキャルピング用のチャート分析ツール。HyperSBI2 由来の tick から生成した1分足/5分足チャート（`source: hypersbi2_tick`）を表示し、ローソク足の上に**書き込み（線/矢印/テキスト/スタンプ/計測 等）**ができる。Scalping Notebook(別アプリ)から URL 経由で開かれることもある。

---

## 2. 技術スタック / 全体構成

- **React 18 UMD**。`ce` = `React.createElement`。hooks: `useState/useRef/useEffect/useMemo`。JSX は使わず全部 `ce(...)`。
- **Canvas 2D 直接描画**でチャート＆書き込みをレンダリング。
- **ストレージ**：
  - チャートデータ本体 → **IndexedDB**（DB名 `ca_cache_v1` / store `blobs` / key `data_<id>`）。`caLoadDataAsync(id, cb)` / `caSaveData(id, d)`。
  - メタ一覧 → `localStorage['ca_meta_v1']`（`caLoadMeta`/`caSaveMeta`）。`{id,ticker,name,analysisDate,thumbUrl,savedAt}`。
  - 他キー：`ca_tickers_v1`, `ca_snippets_v1`(スタンプ定義), `ca_tag_*`, `ca_trash_v1` ほか。
  - サムネ → IDB `thumb_<id>` + メモリ `_thumbMemCache`。
- **Firebase** 任意同期（`FbSettingsModal`、各 autosave が PATCH/PUT）。未設定時は fetch が失敗するだけ。

---

## 3. コンポーネント / 主要関数マップ（行番号は動くので**関数名で grep**）

### ページ/モーダル（`ce` で組む React コンポーネント）
- `App()` — ルート。ライブラリ ⇔ エディタ切替、URLパラメータ処理。
- `DraftLibrary(props)` — チャート一覧ページ。銘柄リスト、カレンダー/タグ/スタンプ検索ボタン、チャートを開く `openChart(id)`。
- `ImageAnnotator(props)` — **分析エディタ本体**。`analysisStrokes`(tf別の書き込み配列)・undo/redo・テキスト入力ポータル・autosave を所有。
- `DataChart(props)` — **Canvasチャート＋全描画ツールの操作**（onMouseDown/Move/Up, onTouch*）。書き込み・選択・移動・計測・スタンプ矢印の入力処理が全部ここ。
- `CaChartCard` / `CaCalendarModal` / `CaTagSearchModal` / `CaStampLogModal` / `PatternSearchModal` / `TagManagerPage` / `NotepadPage` / `RefAnalysisPicker` / `VirtualJoystick` / 各 `*Modal`。

### 描画（モジュールスコープの純関数）
- `drawDataChart(...)` — メインのチャート描画（ローソク/EMA/VWAP/グリッド/出来高）。
- `drawAnalysisStroke(...)` — line/dotted/arrow/rect/circle/marker/trade/horizontal の描画。
- `drawAnalysisStrokeExt(...)` — freehand / text / **スタンプ(枠+矢印)** の描画。
- `drawSelectionHighlight` / `drawUnifiedLassoBox` / `drawPointerArrow`。
- `computeEnhancedBars(bars, refBars)` — **前日チャート(ref)があるとき当日EMAを前日最終EMAから連続計算**して上書き（VWAPは当日リセットのまま）。

### データ/ヘルパー（`ca*` 多数、grepしやすい）
- `caLoadMeta/caSaveMeta/caLoadDataAsync/caSaveData/caLoadSnippets/caLoadTagDefs/caLoadTagMap/caGetChartMemo/_caResolveMetaDate/caParseUrlParams` ほか。

---

## 4. データモデル

### bar（チャートの1本）
```
{ t:"HH:MM", o,h,l,c,v, ema9,ema22,ema50,ema200, vwap }
```
- EMA/VWAP は**取り込み(Python)側で事前計算済み**。表示ツールは原則そのまま使う（例外＝`computeEnhancedBars` の前日連続化のみ）。
- EMA係数 α=2/(N+1)（`ema22` は 2/23）。tm 系は `tToMin("HH:MM")` で分に変換。

### stroke（書き込み、`analysisStrokes[tf]` の配列要素。tf は '1m'/'5m'）
```
{ id, type:'line|dotted|arrow|rect|circle|marker|trade|freehand|text|horizontal',
  side:'cur'|'ref', anchors:[{tm, p}, ...], color, width, opacity, ... }
```
- **テキスト/スタンプ**：`type:'text'`、`_snippet:true`(スタンプ時)、`snipId`、`text`、`fontSize`、`fontBold`、`boxW`。
- **スタンプの矢印(pointer)**：
  ```
  pointer:{ rootSide:'top|right|bottom|left',
            rootOff,   // ★左端(アンカー)からの「論理px」距離。文字数/ズームが変わっても根元が動かない正解
            rootFrac,  // 旧方式(枠幅に対する割合)。rootOff 無い旧データの後方互換用
            tipTm, tipP } // 矢先のチャート時間(分)と価格 ← この tipTm が記録される時間
  ```
  - 根元の解決は `pointerRootPtZ(box, pointer, Z)`、設定は `projectBoxPerimeterOff(box,px,py,Z)`。**新規は必ず rootOff を保存**。
  - 文頭の時間表示は `snippetDisplayText(s, baseText)`（pointer有時のみ `"H:MM " + text`。保存テキストは不変）。

---

## 5. 座標系（重要・ハマりどころ）

- Canvas は `ctx.setTransform(dpr,0,0,dpr,0,0)` → **描画は CSS px**。`minToX`/`pToY` は CSS px を返す。
- 地図モデルズーム：`barW = 12*zoom`、`pxPerYen = 3.5*zoom`。`L=layoutRef.current` に `padL,priceTop,priceH,zoom,dpmax,pxPerYen,...` が入る。
- 価格→y は地図モデル式 `priceTop + (dpmax - p)*pxPerYen`（`pToYcss` / `anchorToScreen` 参照。線形式 `pmin/pmax` はサムネ用/近似）。
- DOM オーバーレイ（バナー等）は `containerRef`(position:relative) 直下に absolute、left/top は CSS px（= minToX/pToY と同基準）。
- `tm` = 0時からの分（例 09:39 = 579）。`_caResolveMetaDate(m)` でメタから日付を解決。

---

## 6. 描画ツールの操作フロー（DataChart の onMouseDown 内、**順序が大事**）

- 先頭で `if(ptrEditRef.current && ptrPointerDown(...)) return;`（スタンプ矢印編集を最優先）。
- 早期ブロック `if(drawTool==='text'||drawTool==='lasso')` が**既存テキスト/スタンプのタップを先に処理して return する**（ここを見落として後段に書くと到達しない＝過去のハマり）。
- スタンプ(矢印付き)を「選択(lasso)」or「スタンプ(snippet)」でタップ → **1タップ目=選択+矢印ハンドル表示、2タップ目=テキスト編集**。
- スタンプ新規配置フロー：配置(placing, ドラッグで位置調整→空白タップ) → 根元選択(pickRoot, 枠線タップ) → 矢先編集(editing, 矢先ドラッグで時間確定) → 確定。`ptrEdit={strokeId,phase,side,fromSelect?}`。

---

## 7. 確認/リリース手順（毎回）

```
# 構文/起動チェック（任意・軽量）
python -m http.server 8791   # プロジェクトdirで（バックグラウンド）
# Chrome MCP: http://localhost:8791/index.html?...&_=<n> を navigate → console error 確認 → mount 確認
# 終わったらサーバ停止

# コミット（1依頼=1コミット）
git add index.html
git commit -m "..."   # 末尾に Co-Authored-By
git push origin main
```
- 修正後ユーザーへ：「**Ctrl+Shift+R でハードリロードして試して**」。

---

## 8. このセッションで実装済みの主な機能（参考）

- スタンプに矢印を付けて**矢先のチャート時間を記録**（pointer）。配置ステージ→根元→矢先の段階フロー。
- スタンプ矢印の**再編集**（選択/スタンプ両ツールでハンドル操作、矢先で時間更新）。
- 根元位置を **rootOff（左端基準・ズーム非依存）** で保持＝文字数/プレフィックスで動かない。
- スタンプ編集時カーソルを**文末**に（`ati._snippet`）。
- **スタンプ記録**ページ（`CaStampLogModal`）＋タグ検索への統合（`caCollectStampPlacements`）。
- テキスト編集ツールバーを**画面内にクランプ**（端で確定/削除が切れない）。
- カレンダー/タグ検索モーダル、矢じり形状を標準矢印に統一、ほか。

### 価格帯別出来高（`caVpAggregate` / `drawDataChart` 内 `_vp*`）の現状（2026-10-04 時点）
- 集計元の切替「**1分終値 | ティック**」を表示（`CA_VP_SRC_UI=true`）。既定は**1分終値**（`ca_vp_src_v1`）。
  - 1分終値＝1分足の出来高まるごとを終値に積む（HyperSBI2 と同じ）。ティック＝取込時に歩み値CSVから作った各足の `vp=[価格,出来高,...]`。
- 帯の位置は**両モードとも HyperSBI2 と同じ「価格が帯の上端」**（価格 C の帯 = [C-刻み, C]、右閉じビン）。1分終値・1円刻みは実データで HyperSBI2 と一致確認済み。5円/10円刻みは未照合。
- **POC は常に表示**（点線＋「POC 価格」ラベル＋一番厚い帯を濃く）。ON/OFF トグルは作って取り消した（ユーザー判断：カーソルに追従して動くので必要）。
- 集計外（縦線より右）は足・出来高・指標線を**暗転**。帯は暗転の上に**描き直して暗くしない**（`_vpRects`）。
- 帯の濃さ：POC帯 0.55 / 通常 0.28 / 1px未満 0.12（極薄）。
- 未着手・保留：帯の長さに基準を設けて濃淡2段階にする案（基準＝株数を銘柄ごと等、構想途中で保留）／価格帯別**ティック数**（取込 Python `tick_to_ohlcv.py` の改修が必要。スクリプトはこのリポジトリに無い）／場中リアルタイム同期（HyperSBI2 は大引け後の歩み値CSV保存のみ。ユーザーは断念）。

## 9. 既知の注意点 / データの真実

- OHLC は生tickから集計済み。**高値/安値/出来高は完全一致**、始値/終値は秒内tick順序で平均±1円ほどブレる（不可避・偏りなし）。
- EMA は終値から α=2/(N+1) で正しく計算されている。HyperSBI2 と数円違って見えたのは **HyperSBI2 側の期間設定(20 など)違い** が主因で、ツールのバグではなかった。
- 見た目の差は主に **Y軸フィットが EMA/VWAP の値も含めている**（`priceRange` 計算が ema9/22/50/200/vwap を min/max に入れる）ため。価格基準フィットに変えると HyperSBI2 に近づく（未対応・要望次第）。
- スタンプ矢印の旧データは `rootFrac` のみ＝文字編集でズレる。根元を一度ドラッグし直すと rootOff 化して安定。
