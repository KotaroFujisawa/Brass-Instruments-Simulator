# 音声サンプル

[測定結果](../docs/results/README.md)

すべての WAV は 48 kHz、16 bit、モノラルです。変ロ長調（B♭メジャー）とセルパンのハ長調（Cメジャー）の音階は、A4 = 440 Hz を基準に低い音から順に演奏します。

## 4オクターブの音階

| サンプル | 実音の音域 | 長さ | リポジトリのルートで実行する再生成コマンド |
| --- | --- | --- | --- |
| [ユーフォニアム](euphonium_Bb1_Bb5_major_f_strong_attack.wav) | B♭1〜B♭5 | 34.50秒 | `python src/render_euphonium_ophicleide.py euphonium --extended` |
| [F／B♭ダブルホルン](horn_Bb1_Bb5_major_f_strong_attack.wav) | B♭1〜B♭5 | 34.50秒 | `python src/render_horn_scale.py` |

4オクターブの音階は全29音です。音の長さと無音の間隔は3オクターブ版と同じです。[ブラウザーで試聴](../README.md#ブラウザーで試聴)

## 3オクターブの音階

| サンプル | 実音の音域 | 長さ | リポジトリのルートで実行する再生成コマンド |
| --- | --- | --- | --- |
| [York トランペットと Bach 5C](trumpet_Bach5C_Bb3_Bb6_major_f_strong_attack.wav) | B♭3–B♭6 | 26.31 秒 | `python src/render_trumpet_bach5c.py` |
| [フリューゲルホルン](flugelhorn_Bb3_Bb6_major_f_strong_attack.wav) | B♭3〜B♭6 | 26.31 秒 | `python src/render_euphonium_ophicleide.py flugelhorn` |
| [キー付きビューグル](keyed_bugle_Bb3_Bb6_major_f_strong_attack.wav) | B♭3〜B♭6 | 26.31 秒 | `python src/render_euphonium_ophicleide.py keyed_bugle --no-initial-check` |
| [Conn 8H トロンボーンと Wick 5AL](trombone_5AL_Bb2_Bb5_major_f_strong_attack.wav) | B♭2–B♭5 | 26.31 秒 | `python src/render_trombone_detailed_scale.py` |
| [5AL トロンボーンの音量を上げたフォルテ](trombone_5AL_Bb2_Bb5_major_louder_f_strong_attack.wav) | B♭2–B♭5 | 26.31 秒 | `python src/render_trombone_detailed_scale.py --louder` |
| [5AL トロンボーンのアタックを強めた音階](trombone_5AL_Bb2_Bb5_major_stronger_f_strong_attack.wav) | B♭2–B♭5 | 26.31 秒 | `python src/render_trombone_detailed_scale.py --stronger` |
| [BB♭チューバと Yamaha BB-67C4](BBb_tuba_Bb1_Bb4_major_f_strong_attack.wav) | B♭1–B♭4 | 26.31 秒 | `python src/render_tuba_scale.py` |
| [B♭管オフィクレイド](ophicleide_Bb1_Bb4_major_f_strong_attack.wav) | B♭1〜B♭4 | 26.31秒 | `python src/render_euphonium_ophicleide.py ophicleide` |

3オクターブの音階は22音です。各音は初期静止状態から計算し、通常は1.08秒、最後の音は1.65秒とします。各音の後には90 msの無音を入れます。トロンボーンの3種類は表の順に生成すると、強奏版と強いアタック版で直前の版の出力ゲインを参照し、音圧レベルの差を計算できます。

## トロンボーンの試聴用音源

| サンプル | 長さ | 音声処理 |
| --- | --- | --- |
| [強いアタック版のピーク制限付き試聴音源](trombone_5AL_Bb2_Bb5_major_stronger_f_listening.wav) | 26.31 秒 | 試聴用にピークを制限しました。レベルとピーク値は[強いアタック版の測定結果](../docs/results/trombone_5AL_Bb2_Bb5_stronger_f_measurements.json)に記録しています。 |
| [強奏版と強いアタック版を同じゲインで聴き比べ](trombone_5AL_stronger_forte_before_after.wav) | 9.18 秒 | B♭2、B♭4、B♭5の順に、各音を強奏版、強いアタック版の順で再生します。両版を音圧の尺度に戻してから連結し、ファイル全体に共通のゲインを適用しています。 |

シミュレーションの全音階 WAV は、各ファイル内の全音に共通のゲインを適用しています。ファイル間の音圧を比べる際は、[測定結果](../docs/results/README.md)に記録したゲインを使って換算してください。

## セルパンの音階とE3の吹奏圧比較

| サンプル | 実音の音域 | 長さ | リポジトリのルートで実行する再生成コマンド |
| --- | --- | --- | --- |
| [調整前のCメジャー音階](serpent_C2_C4_untuned.wav) | C2〜C4 | 11.10秒 | `python src/render_serpent.py` |
| [調整後のCメジャー音階](serpent_C2_C4_tuned.wav) | C2〜C4 | 11.10秒 | `python src/render_serpent.py --preset data/performance_serpent_tuned.json` |
| [E3の吹奏圧比較](serpent_E3_pressure_comparison.wav) | E3の運指 | 2.22秒 | `python src/render_serpent.py` |

セルパンでは1音の計算時間は0.65秒で、その後に90 msの無音を入れます。E3の比較は1.45、2.15、2.85 kPaの順です。最初の条件ではほぼ無音です。[試聴](../README.md#セルパンの試聴と再計算) · [音程と吹奏圧の測定結果](../docs/results/README.md#セルパンの共鳴と発音)

## 以前の音階

| サンプル | 長さ | リポジトリのルートで実行する再生成コマンド |
| --- | --- | --- |
| [トランペットの高音域比較用音源](trumpet_Bb3_Bb6_major_f_strong_attack.wav) | 26.31 秒 | `python src/render_trumpet_high.py` |
| [熱粘性緩和を含むトランペットの2オクターブ音階](trumpet_Bb3_Bb5_major_f_modern_1p5x.wav) | 18.12 秒 | `python src/render_trumpet_modern.py` |
| [線形管体モデルによるトランペット](trumpet_Bb3_Bb5_major_f.wav) | 12.08 秒 | `python src/render_scale.py --render` |
| [所与の波形を伝搬させたトランペット](trumpet_Bb3_Bb5_major_f_nonlinear.wav) | 12.08 秒 | `python src/render_nonlinear.py` |
| [双方向導波管モデルによるトランペット](trumpet_Bb3_Bb5_major_f_bidirectional_nonlinear.wav) | 12.08 秒 | `python src/render_bidirectional.py` |
| [初期の軸対称モデルによるトランペット](trumpet_Bb3_Bb5_major_f_axisymmetric.wav) | 12.08 秒 | `python src/render_axisymmetric.py` |
| [トロンボーンの標準音階](trombone_Bb2_Bb4_major_f_axisymmetric.wav) | 12.08 秒 | `python src/trombone_axisymmetric.py` |
| [トロンボーンのアタックを強めた2オクターブ音階](trombone_Bb2_Bb4_major_f_strong_attack.wav) | 12.08 秒 | `python src/render_trombone_attack.py --preset data/performance_trombone_attack.json` |

トロンボーンの2オクターブ音階では、先に標準音階を生成すると、強いアタック版との比較に標準版の測定値と時系列データを使えます。

12.08秒の音階では通常の音が0.72秒、最後の音が1.10秒で、音の後に0.06秒の間隔があります。18.12秒のトランペット版ではそれぞれ1.08秒、1.65秒、0.09秒です。

[音声ファイルの一覧](manifest.json)に形式、長さ、SHA-256チェックサムを記録しています。ドライバーやハードウェアが異なると、浮動小数点演算の結果にわずかな差が生じることがあります。
