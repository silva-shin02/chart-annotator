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
   - 解釈が割れそうなら、**実装前に確認**する。**質問は選択肢形式（AskUserQuestion）で出す**（2026-10-17 ユーザー明示「質問は選択肢形式で。Claudeアプリ全体の話として」。旧：普通の文章で聞く、は廃止）。
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
- `CaTagSelector`（カード/エディタのタグ選択パネル＋管理モード）/ `CaVpLadder`（全板パネル）。

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
- スタンプ新規配置フロー（2026-10-17〜）：配置(placing, ドラッグで位置調整→空白タップ) → **矢先編集(editing)**（根元選択 pickRoot は省略。仮の矢先＝枠の下辺中央から真下35px（2026-10-17 に70→35））→ 矢先をドラッグ/タップ → 確定。新規配置中は**根元＝矢先の真上の枠の辺**（`ptrRootAboveTip`：矢先が枠より下→下辺、上→上辺、横幅の外なら辺の端）。この自動の根元は `pointer.rootVert=true` を保存し、描画時は rootOff ではなく**矢先の x から直接**根元を求める（横の倍率 `innerW/uSpan` はズーム・画面幅に正比例しないため、rootOff だとズーム/リサイズで傾いた。2026-10-17 修正）。根元つまみを手で動かすと `ptrEdit.rootManual=true`・`rootVert=false` で以後自動をやめる。選択からの再編集（fromSelect）は自動なし。`ptrEdit={strokeId,phase,side,fromSelect?,rootManual?}`。矢先の時刻は**足の中央にぴったり**（`ptrSnapTipTm`：1分足=整数分・5分足=一番近い5分足の開始分）。描くときも矢先の x は足の中央（`ptrTipBarTm`＝時刻表示と同じ丸め）をヒゲと同じ `Math.round(x)+0.5`（`ptrTipPx`）に合わせる（2026-10-18・吸着前の旧データもヒゲにそろう）。矢先/根元の丸点の近く（18px以内）をクリックしただけでも、その位置へ移す（つまみを掴んだ瞬間に `ptrPointerMove` を1回呼ぶ）。

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
- **クラウドセッションの実際の手順**（2026-10 時点）：`git fetch origin main && git checkout -B <作業ブランチ> origin/main` → 編集 → 構文チェック → commit（末尾に `Co-Authored-By` と `Claude-Session`）→ push → GitHub MCP で PR 作成（**draft で作られるので `update_pull_request draft:false` にしてから** `merge_pull_request`）→ マージ後 `git merge --ff-only origin/main && git push` で作業ブランチをマージコミットまで進めておく（やらないと Stop hook が「未プッシュ1件」と言う）。
- 構文チェックの実際：`index.html` の `<script>`（src無し）を抜き出し、`new Function(JSON.stringify(本文))` を並べた js を node で実行。
- 実データでのロジック検証は可（ユーザーがアップロードした JSON/CSV を `/root/.claude/uploads/...` から読む。index.html から関数を抜き出して node で実行）。UI 操作の検証はしない（ルール3）。

---

## 8. このセッションで実装済みの主な機能（参考）

- スタンプに矢印を付けて**矢先のチャート時間を記録**（pointer）。配置ステージ→根元→矢先の段階フロー。
- スタンプ矢印の**再編集**（選択/スタンプ両ツールでハンドル操作、矢先で時間更新）。
- 根元位置を **rootOff（左端基準・ズーム非依存）** で保持＝文字数/プレフィックスで動かない。
- **矢印付きスタンプの枠を動かしても矢印の傾きを保つ**（2026-10-17・DataChart `keepPointerAngle`）：矢先（tipTm/tipP＝記録時刻）は固定、「矢先→元の根元」の直線が新しい枠と最初に交わる点を新しい根元に（rootSide/rootOff を付け直す）。当たらない（角を越える）ときは直線に一番近い角へ。単体移動・投げ縄移動の確定とプレビュー両方。
- **矢印ツールの線を本体ごと動かしても矢先は固定**（2026-10-17・`caMoveAnchors`）：type 'arrow' は矢じり側＝`anchors[0]` を固定し根元側だけ動く。投げ縄・1本ドラッグとも（確定とプレビュー）。端点つまみは従来どおり。
- スタンプ編集時カーソルを**文末**に（`ati._snippet`）。
- **スタンプ記録**ページ（`CaStampLogModal`）＋タグ検索への統合（`caCollectStampPlacements`）。
- テキスト編集ツールバーを**画面内にクランプ**（端で確定/削除が切れない）。
- カレンダー/タグ検索モーダル、矢じり形状を標準矢印に統一、ほか。
- **タッチ端末の精度対策（2026-10-05）**：①価格帯別出来高のつまみ(`vpDragStart`)を**相対ドラッグ**化（触れた位置に縦線が飛ばない）／③選択バーに**端点ナッジ行**（始点/終点切替＋←→↑↓で1足(5分足は5分)/1円、連続タップは700ms後に1回だけ履歴確定。`IS_TOUCH`のみ）。②**価格帯別出来高の長押し**（`vpLpArm`系・表示範囲モードの指のみ）：450ms静止で縦線を指のx位置へ置き、指の上に時刻吹き出し(`vpBubRef`)、動かすと追従、離すと確定。書き込み上/ペン/2本指/10px以上動いたときは発動しない。※長押しは**価格帯別出来高の時刻だけ**（線などの描画には入れない＝ユーザー指定）。

- **バリューエリアと前日の目安線**（2026-10-24）：`caVpValueArea`（POC と同じ pocMap で POC から上下の多い方を足して70%＝`CA_VA_FRAC`）→ `caVpAggregate` が `vah/val` を返す。当日 VAH/VAL は価格帯別出来高と同じ範囲・つまみ/カーソル追従で緑の点線（`CA_VA_COL`）＋POC ラベルと同じ x にラベル。前日の目安線＝`prevCloseInfo.lv`（前日1日全体の POC/VAH/VAL（ティック無ければ1分終値）・約定足の高値/安値）を細い点線＋ラベル（`CA_PREV_LV_COLS`・画面外は出さない）。設定の指標 ON/OFF に `prevLevels`（既定 ON）。
- **スタンプのその後の値動き**（2026-10-24・`CaStampLogModal`）：`caStampForward`＝矢先の足の終値（5分足は5分足の最後の1分足）を基準に、1〜5本後（`CA_STAMP_FWD_N`・1分足の本数）の終値変化率・その間の最大の伸び(高値)/逆行(安値)%。`caCollectStampPlacements` の各件に `fwd`。右ペイン上に表（件数・平均・上昇率・最大の伸び・最大の逆行）、各行に1〜5分後の変化率と5分間の伸び/逆行。この端末(IDB)にあるチャートのみ。
- **ボラ率の並び替え＋カード表示**（2026-10-23・DraftLibrary の銘柄内チャート一覧）：ボラ率＝前場（9:00〜11:30・tm 540〜690）の1分足ごとの (高値−安値)÷終値 の平均 %（`caCalcVolAm1m`。寄りの足を含む・出来高0の足も値幅0で数える）。並び替えに「ボラ ↓/↑」（`vol_desc/vol_asc`・このときは年月見出しを外して1列・未計算は末尾）。カードのタイトル行右に常に「ボラ 0.123%」（計算中は …）。キャッシュは localStorage `ca_vol_am1m_v1` `{id:{v,sa}}`（sa=メタ savedAt が変われば再計算・Firebase 同期なし）。未計算分は銘柄を開いたときに IDB→無ければ Firebase から読んで計算（並列3）。
- **「◀ 前の日」「次の日 ▶」ボタン**（2026-10-18・エディタ上段の ⚙ 設定 の左。シミュ中は非表示）：同じ銘柄でメタの日付（`_caResolveMetaDate`）が直前/直後のチャートへ（ImageAnnotator `dayNav`・同じ日付は除く・無ければ無効表示）。移動は検索の ◀▶ と同じ `saveAndExit(after)`→App `onSearchNav`→DraftLibrary `navOpenId`。同時に「🔎 似た形」「📐 形状登録」ボタンを廃止、ホームの「📐 チャート形状」（形状カタログ）ボタンも廃止（ボタンのみ削除。分割比較・形状撮影・カタログのコードは残置）。
- **前日終値の水平線**（2026-10-18）：当日より前で一番近い日付の同銘柄チャートの最後の約定足（v>0）の終値に灰色の点線（`CA_PREV_CLOSE_COL`）＋左端に「前日終値 価格  M/D(曜)」。画面外なら上/下端に ▲/▼ ラベルだけ。出所は ImageAnnotator `prevCloseInfo`（前日チャート表示中は refAnalysis、無ければ EMA 連続化用の `emaSeedData`）→ DataChart `prevClose` → `drawDataChart` 第21引数。設定の「指標の表示 ON/OFF」に `prevClose` を追加（既定 ON）。Y軸フィットには含めない。分割比較ペイン・サムネには出さない。
- **十字カーソルの価格ラベルは左右両方の価格軸に表示**（2026-10-13。右は全板パネルで隠れるため。連動カーソルも同様）。
- **↶↷（undo/redo）はメタ行（ticker〜価格帯別出来高設定の行）の右端に固定**（2026-10-13。旧：画面右上の浮遊ボタン＝ツールバー/チャート/全板と重なったため廃止）。全板パネルはメタ行の下から（`metaRowH` を ResizeObserver で測定）。
- **タグ選択パネルの一覧は複数列**（`renderItems`。通常モード=2列固定・左列→右列の順／管理モード=CSS columns `columnWidth:300` で幅に応じて1〜複数列。`CaTagSelector` 内は `IS_TOUCH` 分岐なしのコンパクト寸法）。
- **タグ選択パネルの管理モード**（2026-10-11・`CaTagSelector`、カード/エディタ共通）：「✎ 管理」で追加/名前変更(タップ)/色変更(丸をタップ→`ColorPicker`)/カテゴリ移動(セレクト・カテゴリがあるときのみ)/削除/並べ替え(▲▼=同じカテゴリ内で隣と交換。タブレットでHTML5ドラッグが効かないためボタン式)。保存は `caSaveTagDefsSync`（`TagManagerPage` と共用・Firebase同期込み）。変更後 `ca_tag_defs_changed` を発火→カードとエディタのチップが再描画。カテゴリは**追加のみ**(`caSaveTagCatsSync`・管理中は空カテゴリも見出し表示。改名・削除・並べ替えはタグ管理ページ)。新規タグの追加先カテゴリは入力欄横のセレクトで選ぶ(カテゴリがあるとき。既定=未分類)。削除はタグ割当も掃除。

### 価格帯別出来高（`caVpAggregate` / `drawDataChart` 内 `_vp*`）の現状（2026-10-04 時点）
- **帯の刻みは1円固定**（2026-10-14・自動/1円/5円/10円の切替を廃止。`vpOpt.bin='1'`。旧キー `ca_vp_bin_v1` は未使用）。
- 集計元の切替「**1分終値 | ティック**」を表示（`CA_VP_SRC_UI=true`）。既定は**ティック**（2026-10-13〜。`ca_vp_src_v1` に 'close' を保存した端末のみ1分終値）。
  - **ティック＝HyperSBI2 全板の「出来高」列と同じ数字**（10/13 9984 15:30 で全板の28行＋OVER/UNDER と完全一致を確認）。1分終値は HyperSBI2 チャート上の価格帯別出来高の積み方で、全板とは一致しない。
  - 1分終値＝1分足の出来高まるごとを終値に積む（HyperSBI2 と同じ）。ティック＝取込時に歩み値CSVから作った各足の `vp=[価格,出来高,...]`。
- 帯の位置は**両モードとも HyperSBI2 と同じ「価格が帯の上端」**（価格 C の帯 = [C-刻み, C]、右閉じビン）。1分終値・1円刻みは実データで HyperSBI2 と一致確認済み。5円/10円刻みは未照合。
- **POC は常に表示**（点線＋「POC 価格」ラベル＋一番厚い帯を濃く）。ON/OFF トグルは作って取り消した（ユーザー判断：カーソルに追従して動くので必要）。
- 集計外（縦線より右）は足・出来高・指標線を**暗転**。帯は暗転の上に**描き直して暗くしない**（`_vpRects`）。
- **5分足チャート×「1分終値」**（2026-10-06）：5分足の終値に5分足1本ぶんの出来高を積む（`caVpAggregate` の `closeBars`=`data.bars_5m`）。ティックは5分足でも従来どおり1分足の `vp`。指定時刻が足の途中のとき、その5分足は丸ごと含む。
- **帯の長さの平均線**（2026-10-08。**2026-10-14〜常時表示**＝OFF/ONスイッチ廃止・`vpOpt.avg=true` 固定。旧キー `ca_vp_avg_v1` は未使用）：平均＝出来高のある帯の合計出来高÷帯の本数（空の帯は数えない）。帯と同じ縮尺の位置に縦の点線＋「平均 ◯◯株」(琥珀色)。帯の長さ＝その帯の出来高÷集計範囲の最大帯×描画域幅の**40%**（2026-10-17 に25%→40%・定数 `CA_VP_MAXW_FRAC`）（ズーム・価格・銘柄の絶対出来高に依存しない相対表示）。
- **全板パネル**（2026-10-13・`CaVpLadder`、設定行の「全板」ボタンで開閉。**2026-10-14〜既定で開いた状態**（`vpLadOpen` 初期値 true・保存なし）、チャート領域 `splitContainerRef` の右端に absolute オーバーレイ）：**常にティック**で寄り〜集計時刻（`vpLadderCut`＝指定時刻まで/固定/カーソル、無ければ最新の約定足）の値段ごと出来高。1円（呼値が粗ければ呼値）ごと全行、出来高数字＋横棒＋値段。現在値の行=黄、POC=紫、OVER/UNDER=見えている行より上/下の合計。現在値が変わると中央へ。行タップ→`vpOpt.selP`→`drawDataChart` がその値段に水平線（シアン点線）＋集計範囲内でその値段が約定した足に点（大きさ=その足での出来高、5分足は5分ごと合算）。再タップ/閉じるで解除。
- **ホームの検索パネル（DraftLibrary・タグ/スタンプ/テキストの3タブ）**（2026-10-17 作り直し）：並びはチャートの日付（`_caResolveMetaDate` に統一）の新しい順。「銘柄別」グループは各銘柄の最新日付が新しい順。テキスト検索 `doSearch` の対象＝チャート名・銘柄名/コード・タグ名・チャートメモ・形状メモ・書き込みのテキスト/スタンプ（`caSnipEffText`＝定義の文字）。表記ゆれ吸収 `_srchNorm`（NFKC・小文字・カタカナ→ひらがな）。この端末に無いチャートは Firebase から取得し、検索用の文字だけ IDB `srch_<id>`（savedAt が同じ間は再利用。`data_<id>` には書かない）。並列4・進捗表示。
- **検索から開いたチャートの戻り/前後移動**（2026-10-17・A/B/C）：検索結果を開くと `openFromSearch` が検索パネルの状態を `_caSrchKeep`、結果の並びを `_caSrchNav` に残す（モジュール変数）。A=エディタから戻ると検索パネルをそのまま復元（語・結果・絞り込み・タブ・スクロール位置、直前に開いた行を青枠）。B=エディタ上端に「🔍 語 ◀ n/N ▶ 一覧へ」バー（`goSearchNav`。別チャートへは `saveAndExit(after)`＝旧「終了→はい」の保存処理を確認なしで実行→App `onSearchNav`→DraftLibrary `navOpenId` で次を開く。同じチャート内の次ヒットはその場で移動）。C=注釈/スタンプでヒットしたときは開いた直後にその時刻を画面中央へ（`focusSearchHit`・1枚表示で足種が違えば切替）、書き込みを1.8秒囲む（`_caFlashStrokeId`→`drawDataChart`）。テキスト検索の書き込みキャッシュは `srch2_<id>`（stroke id 入り）。
- **SN タグ表示（✦チップ）は全廃**（2026-10-14・タグは CA で付けて SN に表示する方針＝SN 側 `_caTagsRefresh` 等）。エディタのメタ行・チャートカード・カレンダー・タグ検索（「SN タグ」欄と結果カード）から削除。`caLoadSnChartShapeTags` はコンソール診断 `caDebugSN` 用に残置。
- **全板パネルで十字カーソルの値段の行をハイライト**（2026-10-14・青背景＋白太字。DataChart `vpReportCursorP`→`onVpCursorP`→親 `vpLadCurSubRef`→`CaVpLadder` の `hovP`。親は再レンダーしない。カーソルの値段の行を常に中央へ。カーソルが消えたら（チャート外・出来高域・価格軸・全板の上）**現在値=黄（固定時は固定時刻の終値）を中央へ戻す**（2026-10-14）。全板パネル上でマウスを乗せた行も同じ青に（`ladHovP`・こちらは中央寄せ/スクロールしない）。1分足/5分足どちらのペインのカーソルでも。前日側・出来高域は対象外）。
- **縦線（集計の境目）は指定時刻の足の真ん中**（2026-10-13・`_vpLineX`＝つまみ位置も同じ。5分足はその時刻を含む足の中央）。暗転の境目 `_vpCutX` は従来どおり足の右端（指定した足は暗くしない）。つまみ「← HH:MM →」の時刻部分はドラッグで左右にスライド（相対ドラッグ・足単位で吸着）、←→は1分ずつ。
- 帯の濃さ：POC帯 0.55 / 通常 0.28 / 1px未満 0.12（極薄）。
- 未着手・保留：帯の長さに基準を設けて濃淡2段階にする案（基準＝株数を銘柄ごと等、構想途中で保留）／価格帯別**ティック数**（取込 Python `tick_to_ohlcv.py` の改修が必要。スクリプトはこのリポジトリに無い）／場中リアルタイム同期（HyperSBI2 は大引け後の歩み値CSV保存のみ。ユーザーは断念）。

## 9. 既知の注意点 / データの真実

- OHLC は生tickから集計済み。**高値/安値/出来高は完全一致**、始値/終値は秒内tick順序で平均±1円ほどブレる（不可避・偏りなし）。
- EMA は終値から α=2/(N+1) で正しく計算されている。HyperSBI2 と数円違って見えたのは **HyperSBI2 側の期間設定(20 など)違い** が主因で、ツールのバグではなかった。
- 見た目の差は主に **Y軸フィットが EMA/VWAP の値も含めている**（`priceRange` 計算が ema9/22/50/200/vwap を min/max に入れる）ため。価格基準フィットに変えると HyperSBI2 に近づく（未対応・要望次第）。
- スタンプ矢印の旧データは `rootFrac` のみ＝文字編集でズレる。根元を一度ドラッグし直すと rootOff 化して安定。

## 10. 引継ぎ（2026-10-13 時点・前セッション PR #12〜#26）

### 直近で入れたもの（詳細は §8）
- タッチ精度対策（価格帯別出来高のつまみ相対ドラッグ・長押し、端点ナッジ）。
- 価格帯別出来高：5分足×1分終値＝5分足終値ベース／平均線スイッチ／**既定をティックに**／**全板パネル**（行タップで水平線＋約定足の点）／縦線を足の中央に。
- タグ選択パネル：管理モード（追加・改名・色・カテゴリ移動・カテゴリ追加・削除・▲▼並べ替え）、2列表示、エディタ側は縦スクロール（40vh）。
- ↶↷ をメタ行右端に固定、十字カーソルの価格を左軸にも。

### 検証済みの事実
- **ティック集計＝HyperSBI2 全板の「出来高」列**：10/13 9984 15:30、全板の表示28行＋OVER/UNDER が完全一致（1分終値はほぼ全不一致）。全板は注文の無い値段の行を省く（5,317/5,316/5,313 など）が、ツールは1円ごと全行。
- 足の出来高 v と sum(vp) は一致（10/13 9984：49,524,400 株、CSV 直集計とも一致）。

### 未解決・保留（ユーザーの返事待ち/要望次第）
- 「**POC以外の帯が短く見える**」（2026-10-17 案A＝最長帯を25%→40% を実施。まだ短ければ案B＝寄り板寄せを基準から除外）：原因の見立て（最大帯基準の比例・寄り板寄せ・1分終値の尖り）と選択肢（そのまま／寄り板寄せを長さ基準から除外★推奨／上位5%基準／平方根）を提示したまま返事なし。※その後既定がティックになったので見え方が変わっている可能性あり。
- 「**タグ管理の文字が大きい**」：管理モード（`CaTagSelector`）を小さくした。ホーム画面の全画面 `TagManagerPage` のことだった場合は未対応。
- ~~全板パネルとチャートの縦線の食い違い~~ → 2026-10-14 解消：固定もカーソルも無いとき全板は**上のチャートの表示範囲の中央の足**まで（DataChart が `layoutRef.vpCenterTm` を `onVpCenterTm` で親 `vpCenterTm` へ→`vpLadderCut`）。チャートから全板へ移ったときもカーソルの時刻は持ち越さない（#35 の持ち越しはユーザー指定で廃止）。
- つまみの ←→ は常に1分刻み（5分足ペインでも）。
- 価格帯別出来高 5円/10円刻みの HyperSBI2 照合は未実施。濃淡2段階案・価格帯別ティック数・場中リアルタイム同期は §8 のとおり保留。

