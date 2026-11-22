# 公開測定結果

[音声サンプル](../../samples/README.md)

公開した音声の計算値と解析結果です。音声生成や検証のスクリプトを再実行すると、`output/` に新しいレポートが出力されます。ユーフォニアム、オフィクレイド、ダブルホルン、フリューゲルホルン、キー付きビューグルのレポートでは、`render` に生成時の測定値を、`independent_wav_check` に書き出したWAVを独立に解析した結果を記録しています。`filename` とSHA-256で [公開ファイルの一覧](../../samples/manifest.json) と照合できます。

## ユーフォニアム・オフィクレイド・ダブルホルン

| レポート | 実音域 | 音数 | 長さ | 持続部の最大音程差 |
| --- | --- | ---: | ---: | ---: |
| [ユーフォニアム](euphonium_Bb1_Bb5_verified_measurements.json) | B♭1〜B♭5 | 29 | 34.50秒 | 13.3セント |
| [B♭管オフィクレイド](ophicleide_verified_measurements.json) | B♭1〜B♭4 | 22 | 26.31秒 | 12.5セント |
| [F／B♭ダブルホルン](horn_verified_measurements.json) | B♭1〜B♭5 | 29 | 34.50秒 | 13.9セント |

3つのWAVにクリッピングはありません。ユーフォニアムはC2・D2の発音初期に、オフィクレイドはC3・E♭4・G4の発音初期と持続部に弱い周期倍化が見られました。ダブルホルンはF管を12音、B♭管を17音で使用しました。

## フリューゲルホルンとキー付きビューグル

| レポート | 実音域 | 音数 | 長さ | 持続部の最大音程差 |
| --- | --- | ---: | ---: | ---: |
| [フリューゲルホルン](flugelhorn_verified_measurements.json) | B♭3〜B♭6 | 22 | 26.31秒 | 13.5セント |
| [キー付きビューグル](keyed_bugle_verified_measurements.json) | B♭3〜B♭6 | 22 | 26.31秒 | 12.8セント |

両方のWAVでクリッピングは0サンプルでした。フリューゲルホルンのE♭4・G5と、キー付きビューグルのE♭6・F6・G6・A6には弱い周期変調が見られます。ビューグルは19音で開孔からの放射を確認しました。B♭5を超える7音は史料の7キー運指表を上に拡張した試算です。[モデルと再計算手順](../ja/FLUGELHORN_KEYED_BUGLE_MODEL.md)

## 3オクターブの音階とモデルの検証

| レポート | 内容 |
| --- | --- |
| [Bach 5C を使ったトランペット](trumpet_Bach5C_Bb3_Bb6_measurements.json) | 22音の計算結果と、生成した PCM ファイルを別途解析した結果 |
| [トランペットの高音域比較データ](trumpet_high_measurements.json) | Bach 5C 版との比較に使った以前の B♭3–B♭6 の結果 |
| [Wick 5AL を使ったトロンボーン](trombone_5AL_Bb2_Bb5_measurements.json) | B♭2–B♭5 の各音の計算結果と、生成した WAV の独立した解析 |
| [5AL トロンボーンの音量を上げたフォルテ](trombone_5AL_Bb2_Bb5_louder_f_measurements.json) | 詳細形状を使った5ALの標準音階を基準とした、音圧レベルと PCM レベルの比較 |
| [5AL トロンボーンのアタックを強めた音階](trombone_5AL_Bb2_Bb5_stronger_f_measurements.json) | 発音時刻をそろえた区間と固定時刻の区間におけるアタックの比較、持続部のレベル、ピークを制限した試聴音源の測定値 |
| [Yamaha BB-67C4 を使ったBB♭チューバ](BBb_tuba_Bb1_Bb4_measurements.json) | B♭1–B♭4 の計算結果と PCM の独立した解析。発音のタイミングと発音初期の低音の変調を含みます。 |
| [トランペットのテーパーとベルの比較](bell_comparison.json) | 以前のテーパー、細分化したテーパー、連成した管外放射モデルを比較した結果。[テーパーの図](../figures/trumpet_taper_refinement.png) |
| [ベル境界の検証](bell_boundary_verification.json) | CUDA 計算のベル境界の圧力と、CPU で周波数領域から再構成した圧力の比較 |
| [ベルの管外放射の検証](bell_exterior_verification.json) | 開口面でのモードへの射影、状態空間モデルの近似、受動性、受音点への伝達特性の確認 |
| [トランペットのマウスピース比較](trumpet_mouthpiece_results.json) | 以前のマウスピース形状と Bach 5C の実測輪郭を用いたモデルで、形状、インピーダンス、吹奏時の結果を比較。[インピーダンスの図](../figures/mouthpiece_impedance.png) |

## セルパンの共鳴と発音

| レポート | 内容 |
| --- | --- |
| [運指と吹奏圧の測定結果](serpent_measurements.json) | 入力インピーダンス、調整前の音階、E3の吹奏圧比較、WAVの独立再測定 |
| [調整前後の音程比較](serpent_tuned_measurements.json) | 実音C2〜C4の調整前後の周波数、音程差、持続部の周期性 |

調整前は15音中13音で周期的な発音が得られました。調整後は15音すべてで周期的な発音が得られ、14音が目標から±15セント以内でした。D3は143.13 Hzで、目標の146.83 Hzより約44セント低い結果でした。[共鳴の図](../figures/serpent_intonation.png) · [モデルと再計算手順](../ja/SERPENT_MODEL.md)

## 以前の結果

| レポート | 内容 |
| --- | --- |
| [トランペットの2オクターブ音階の測定](trumpet_modern_measurements.json) | 各音の音高、発音初期と持続部の音高推定、圧力、周期性、ソルバーの設定 |
| [トランペットの2オクターブ音階の検証](trumpet_modern_verification.json) | 弱いパルスによる入力インピーダンス、ベルの反射係数の大きさ、B♭4のフィードバックの確認 |
| [Euler ソルバーの試験](axisymmetric_solver_tests.json) | 静止状態、保存性、Sod 衝撃波管の格子細分化、円筒管の半径方向モードの確認 |
| [初期の軸対称モデルによるトランペット](trumpet_axisymmetric_measurements.json) | 以前の軸対称モデルによる音階の音ごとの結果 |
| [トロンボーンの測定](trombone_measurements.json) | 標準音階の結果、プリセット、音ごとの診断値 |
| [トロンボーンの形状検証](trombone_geometry_verification.json) | マウスピースの容積と共鳴、スライド長、インピーダンスのピーク |
| [トロンボーンの連成検証](trombone_coupling_tests.json) | B♭3のフィードバックと、格子を細分化した場合の検証 |
| [トロンボーンのアタックを強めた2オクターブ音階](trombone_strong_attack_measurements.json) | アタックの設定、発音時刻の比較、音高とレベルの変化 |
| [線形管体モデルによるトランペット](trumpet_linear_measurements.json) | 初期の CPU 版の音階 |
| [双方向モデルによる CPU 版トランペット](trumpet_bidirectional_measurements.json) | 非線形モデルと線形モデルを比較した指標 |
| [所与の波形を伝搬させたトランペット](trumpet_one_way_measurements.json) | 非線形伝搬の指標と、条件をそろえた基準音源との比較 |

記録した計算時間は、ハードウェアや計算時に並行して動いていた処理に依存します。`common_gain_fs_per_pa` や `gain_fs_per_pa` などのフィールドには、それぞれの音声生成時に PCM へ変換するために適用したゲインを記録しています。
