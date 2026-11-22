# 形状データ、演奏設定、出典

長さはメートル、周波数はヘルツで記録しています。別の単位を使う場合は項目名に示します。管体の表には、曲がった管を展開した中心線に沿う距離を記録しています。元の図と推定した寸法は、[モデルの説明](../docs/models.md)と[参考文献](../docs/references.md)にまとめています。

| ファイル | 内容 |
| --- | --- |
| `york_trumpet_fig7_52.csv` | *The Science of Brass Instruments* の図7.52から読み取ったYorkトランペットの距離と管径 |
| `bach_5c_jackson_2025_fig2.csv` | JacksonとScavone（2025）の図2にあるBach 5Cの実測輪郭から読み取った軸方向距離と半径 |
| `conn8h_fig4_22.csv` | 再構成したConn 8H管体の距離と半径。マウスピース入口から80 mmの位置に始まる |
| `wick5al_calibrated.csv` | 寸法と音響特性を校正したDenis Wick 5ALの距離と半径 |
| `alexander_bb_tuba_reconstructed.csv` | AlexanderのC管からBB♭管に換算したチューバの管体。ソルバー内で軸方向寸法を0.936倍する前の形状 |
| `yamaha_bb67c4_reconstructed.csv` | 寸法と容積の計測値から再構成したYamaha BB-67C4の内面形状 |
| `euphonium_bore_fig221.csv` | *The Science of Brass Instruments* の図2.21から読み取ったユーフォニアムの管形状 |
| `boosey_euphonium_mouthpiece_reconstructed.csv` | Boosey & Co.の収蔵個体13.15の採寸を使ったマウスピース内面の再構成 |
| `ophicleide_gautrot_eu3590.csv` | Gautrot製B♭管バス・オフィクレイド（EU3590）の公表管径から再構成した管形状 |
| `horn_bb_bore_fig734.csv` | *The Science of Brass Instruments* の図7.34から読み取ったAlexander製ダブルホルンB♭側の管形状 |
| `alexander_8m_mouthpiece_reconstructed.csv` | Alexander 8Mの公称寸法と教科書のカップ曲線から再構成したマウスピース内面 |
| `flugelhorn_cerveny_eu3664_fig7_20.csv` | 教科書の図7.20から読み取ったČervený製B♭管フリューゲルホルン（EU3664）の管体 |
| `yamaha_fh11f4_reconstructed.csv` | Yamaha FH-11F4の公称リム内径とスロート径を使って再構成したUカップとバックボア |
| `keyed_bugle_halari_eu907.csv` | 図7.20から読み取ったHalari製7キーC管（EU907）の管体と、同時代の標本寸法から補完したベル端 |
| `keyed_bugle_toneholes_06872.csv` | 同時代の7キーC管（NMM 06872）の指穴位置と半径、および推定チムニー高 |
| `model.json` | 初期のトランペットモデルのカップ深さと、単体マウスピースの校正に使った共鳴周波数 |
| `performance.json` | 線形管体モデルによるトランペットの演奏設定 |
| `performance_bidirectional.json` | CPUの双方向伝搬モデルによるトランペットの演奏設定 |
| `performance_axisymmetric.json` | 初期の軸対称モデルによるトランペットの演奏設定 |
| `performance_trumpet_modern.json` | 三次剛性と熱粘性損失を追加したトランペットの2オクターブ音階の音別設定 |
| `performance_trumpet_high.json` | B♭3〜B♭6に拡張したトランペットの音階とアタック設定 |
| `performance_trumpet_bach5c.json` | Bach 5Cの形状と外部音場を連成したトランペットの音別補正 |
| `performance_trombone.json` | トロンボーンの音名、スライド位置、唇の設定、吹奏圧、管長補正 |
| `performance_trombone_attack.json` | アタック時の吹奏圧を調整したトロンボーンの演奏設定 |
| `performance_trombone_detailed_scale.json` | 5ALを使ったトロンボーンの3オクターブ音階の補正と高音域の設定 |
| `performance_trombone_stronger_forte.json` | トロンボーンの `--stronger` 版に使う調律補正 |
| `performance_tuba.json` | B♭1〜B♭4のチューバの唇、吹奏圧、アタック、バルブ、管長補正 |
| `performance_euphonium.json` | B♭2〜B♭5のユーフォニアムの唇、吹奏圧、4バルブの運指、管長補正 |
| `performance_euphonium_pedal.json` | ユーフォニアムの4オクターブ版に追加するB♭1〜A2の7音の設定 |
| `performance_ophicleide.json` | B♭1〜B♭4のオフィクレイドの唇、吹奏圧、キーで開ける側孔、管長補正 |
| `performance_horn.json` | B♭1〜B♭5のダブルホルンの唇、吹奏圧、F管／B♭管の選択、バルブ、倍音次数、管長補正 |
| `performance_flugelhorn.json` | B♭3〜B♭6のフリューゲルホルンのバルブ番号、唇、吹奏圧、アタック、有効管長の補正 |
| `performance_keyed_bugle.json` | B♭3〜B♭6のキー付きビューグルの実音、記譜音、開孔番号、唇、吹奏圧、アタック、有効管長の補正 |
| `sources.json` | 初期のトランペットの管体、マウスピースの再構成、唇モデルの出典 |
| `nonlinear_sources.json` | 入射波を指定する非線形伝搬モデルの式と仮定 |
| `sources_bidirectional.json` | CPUの双方向伝搬モデルの文献と仮定 |

演奏設定の `target_hz` は目標周波数、`lip_frequency_hz` は唇の固有振動数、`blowing_pressure_pa` は吹奏圧、`rest_y_m` は静止時の開口の設定です。トランペットの `valves_semitones` は、押した各バルブが下げる公称半音数を並べたものです。チューバの `valves` はバルブ番号1〜4を記録し、第1〜4バルブは順に2、1、3、5半音下げる設定です。`tuning_m` と `trim_m` は有効管長の補正量です。トロンボーンの `--louder` 版の吹奏圧の倍率はレンダラーに定義しています。

オフィクレイドの `open_holes` は開く側孔の番号を記録します。ダブルホルンの `side` は `F` または `Bb` です。`note` は実音、`written_note` はF調ホルンの記譜音です。形状を補った箇所や運指の根拠は各解説に記載しています。[ユーフォニアムとオフィクレイド](../docs/ja/EUPHONIUM_OPHICLEIDE_MODEL.md) · [ダブルホルン](../docs/ja/DOUBLE_HORN_MODEL.md)

フリューゲルホルンの `valves` は使用するバルブ番号です。キー付きビューグルの `open_holes` は実際に開く指穴の番号で、ベル側から1〜7番です。第1孔は通常開で、キーを操作して閉じます。B♭5を超える7音の運指は計算上の拡張です。[フリューゲルホルンとキー付きビューグルの形状・運指](../docs/ja/FLUGELHORN_KEYED_BUGLE_MODEL.md)

管体の断面は図から読み取って近似しました。マウスピースの形状は、資料にある輪郭、長さ、容積、共鳴周波数を使って決めています。演奏設定は、それぞれのモデルで目標音を発音するように調整しています。

`bach_5c_jackson_2025_fig2.csv` は公開された図2の座標をサンプリングし、メートルに換算したものです。出典は Miranda Jackson と Gary Scavone による “A study of impedance of brass instruments and mouthpieces,” *Proceedings of Meetings on Acoustics* 58, 035019（2025）です。元の論文は CC BY-NC 4.0 で公開されています。 [論文と元の図](https://doi.org/10.1121/2.0002165) · [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
