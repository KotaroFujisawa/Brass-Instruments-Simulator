# 金管楽器シミュレーター

[日本語ドキュメント一覧](docs/ja/README.md) · [モデルの方程式と仮定](docs/models.md) · [参考文献](docs/references.md) · [形状データと演奏設定](data/README.md)

トランペット、トロンボーン、チューバ、ユーフォニアム、オフィクレイド、F／B♭ダブルホルン、フリューゲルホルン、キー付きビューグル、E♭テナーホルンの音を物理モデルで合成します。Adachi–Satoの2自由度唇モデルをマウスピースと管内音場に連成します。CUDAソルバーは、曲がった管を中心線に沿って展開した軸対称の管内で非線形な波の伝搬を解きます。ベルで放射された音を求めると同時に、管内へ戻る反射波が唇の振動に及ぼす影響も計算します。

## 音声サンプル

各サンプルは実音のB♭メジャー上行音階をフォルテで演奏します。基準音はA4 = 440 Hzです。各音を静止状態から個別に計算してつなぎ、各音を1.08秒、最後のB♭を1.65秒としました。各音の後に90 msの無音を入れています。3オクターブ版は22音で26.31秒、4オクターブ版は29音で34.50秒です。形式は48 kHz、16 bit、モノラルです。

### ブラウザーで試聴

再生ボタンを押すと、その場で音を聴けます。音が出ない場合はプレーヤーのミュートを解除してください。

#### トランペット（Bach 5C、実音B♭3〜B♭6）

https://github.com/user-attachments/assets/651233dd-1de2-4166-8f5f-820ce01c32ef

#### トロンボーン（Denis Wick 5AL、実音B♭2〜B♭5）

https://github.com/user-attachments/assets/f14650f5-a03d-4423-8e90-08169da3e7cf

#### E♭テナーホルン（実音B♭2〜B♭5）

[WAVを開く](samples/tenor_horn_Bb2_Bb5_major_f_strong_attack.wav) · [モデルの説明](docs/ja/TENOR_HORN_MODEL.md)

#### BB♭チューバ（Yamaha BB-67C4、実音B♭1〜B♭4）

https://github.com/user-attachments/assets/14725a97-9721-4e2b-aa10-3815647df5f2

#### ユーフォニアム（実音B♭1〜B♭5）

https://github.com/user-attachments/assets/7abb8c92-bccd-42b8-a587-10e82c34ed69

#### B♭管オフィクレイド（実音B♭1〜B♭4）

https://github.com/user-attachments/assets/0ddcb7b4-f377-4d7e-b65f-2890d1c7e8ff

#### F／B♭ダブルホルン（実音B♭1〜B♭5）

https://github.com/user-attachments/assets/63ab0943-60c4-411d-bc52-bcacbac094dd

#### フリューゲルホルン（実音B♭3〜B♭6）

https://github.com/user-attachments/assets/115cac3d-415c-421b-ac8e-f114999a2f78

#### キー付きビューグル（実音B♭3〜B♭6）

https://github.com/user-attachments/assets/2862e48d-767d-4d86-9b0e-985f30063a8f

### 音源と測定結果

| 音声 | 実音域 | 測定結果 |
| --- | --- | --- |
| [Yorkトランペット、Bach 5C](samples/trumpet_Bach5C_Bb3_Bb6_major_f_strong_attack.wav) | B♭3〜B♭6 | [音程と放射音圧](docs/results/trumpet_Bach5C_Bb3_Bb6_measurements.json) |
| [Conn 8Hトロンボーン、Denis Wick 5AL](samples/trombone_5AL_Bb2_Bb5_major_f_strong_attack.wav) | B♭2〜B♭5 | [基準のフォルテ](docs/results/trombone_5AL_Bb2_Bb5_measurements.json) |
| [トロンボーン、吹奏圧を上げた版](samples/trombone_5AL_Bb2_Bb5_major_louder_f_strong_attack.wav) | B♭2〜B♭5 | [持続時の吹奏圧を15%増加](docs/results/trombone_5AL_Bb2_Bb5_louder_f_measurements.json) |
| [トロンボーン、さらに吹奏圧とアタックを強めた版](samples/trombone_5AL_Bb2_Bb5_major_stronger_f_strong_attack.wav) | B♭2〜B♭5 | [音圧と発音時刻の比較](docs/results/trombone_5AL_Bb2_Bb5_stronger_f_measurements.json) |
| [E♭テナーホルン（アルトホルン）](samples/tenor_horn_Bb2_Bb5_major_f_strong_attack.wav) | B♭2〜B♭5 | [音程・音圧・アタック](docs/results/tenor_horn_verified_measurements.json) |
| [再構成したBB♭チューバ、Yamaha BB-67C4](samples/BBb_tuba_Bb1_Bb4_major_f_strong_attack.wav) | B♭1〜B♭4 | [音程・音圧・発音時刻](docs/results/BBb_tuba_Bb1_Bb4_measurements.json) |
| [ユーフォニアム](samples/euphonium_Bb1_Bb5_major_f_strong_attack.wav) | B♭1〜B♭5 | [音程と放射音圧](docs/results/euphonium_Bb1_Bb5_verified_measurements.json) |
| [B♭管オフィクレイド](samples/ophicleide_Bb1_Bb4_major_f_strong_attack.wav) | B♭1〜B♭4 | [音程と指穴からの放射](docs/results/ophicleide_verified_measurements.json) |
| [F／B♭ダブルホルン](samples/horn_Bb1_Bb5_major_f_strong_attack.wav) | B♭1〜B♭5 | [音程と管の選択](docs/results/horn_verified_measurements.json) |
| [フリューゲルホルン](samples/flugelhorn_Bb3_Bb6_major_f_strong_attack.wav) | B♭3〜B♭6 | [音程・音圧・発音時刻](docs/results/flugelhorn_verified_measurements.json) |
| [キー付きビューグル](samples/keyed_bugle_Bb3_Bb6_major_f_strong_attack.wav) | B♭3〜B♭6 | [音程・音圧・開孔音](docs/results/keyed_bugle_verified_measurements.json) |

トロンボーンのアタックをさらに強めた版では、15%増圧の版から持続時の吹奏圧をさらに25%上げ、吹奏圧の立ち上がりを12 msから6.5 msに短縮しました。ベル正面1 mの放射音圧レベルは、22音の中央値で持続部が+3.8 dB、音が立ち上がってから最初の50 msが+6.0 dBでした。

音階のWAVはファイルごとに一つの出力ゲインを適用しています。2つの演奏に同じゲインを適用した抜粋で、吹奏圧とアタックを変えたときの音圧差を確認できます。音階全体を試聴するためのピークを抑えた版も収録しています。 [同じゲインで聴き比べ](samples/trombone_5AL_stronger_forte_before_after.wav) · [音階全体の試聴版](samples/trombone_5AL_Bb2_Bb5_major_stronger_f_listening.wav) · [以前の音源・再生成コマンド・チェックサム](samples/README.md)

## セルパンの試聴と再計算

6孔のC管セルパンで、実音C2〜C4のCメジャー上行音階を比較します。調整後は15音すべてで持続発音し、14音が平均律の目標から±15セント以内に入りました。D3の持続部は約44セント低い結果です。

- [調整前の音階（11.10秒）](samples/serpent_C2_C4_untuned.wav)
- [唇と吹奏圧を調整した音階（11.10秒）](samples/serpent_C2_C4_tuned.wav)
- [E3の吹奏圧比較（2.22秒）](samples/serpent_E3_pressure_comparison.wav)

E3の比較では、持続吹奏圧を1.45、2.15、2.85 kPaの順に変えます。最初の1.45 kPaはほぼ無音です。

### 調整前の音階

https://github.com/user-attachments/assets/46803d0c-8009-4dd7-992f-a5e1311bebd1

### 調整後の音階

https://github.com/user-attachments/assets/3d5e8b3f-0058-40b5-afe3-2096bc640c5a

### E3の吹奏圧比較

https://github.com/user-attachments/assets/b764cb46-8d4d-4376-a5be-3d75a0e1d289

### セルパンを再計算する

```sh
python src/analyze_serpent.py
python src/render_serpent.py
python src/render_serpent.py --preset data/performance_serpent_tuned.json
```

[モデルと実行手順](docs/ja/SERPENT_MODEL.md) · [共鳴と音程のグラフ](docs/figures/serpent_intonation.png) · [調整前とE3の測定結果](docs/results/serpent_measurements.json) · [調整後の測定結果](docs/results/serpent_tuned_measurements.json)

## インストール

開発にはPython 3.12を使用しました。NumPy、SciPy、Numba、Matplotlibが必要です。リポジトリのルートからコマンドを実行します。

```sh
git clone https://github.com/KotaroFujisawa/Brass-Instruments-Simulator.git
cd Brass-Instruments-Simulator
python -m venv .venv
```

Windows PowerShellでは `.venv\Scripts\Activate.ps1`、Linuxでは `source .venv/bin/activate` を実行して仮想環境を有効にします。その後、依存パッケージをインストールします。

```sh
python -m pip install -r requirements.txt
```

CPUモデルはここまでの設定で実行できます。軸対称モデルにはNVIDIA GPUとドライバー、およびCUDAランタイムコンパイラーのNVRTCが必要です。ソルバーはPythonの `ctypes` を通じてCUDA Driver APIを呼び出します。

```sh
python -m pip install nvidia-cuda-nvrtc-cu12==12.4.127
```

公開音源の計算にはNVIDIA RTX 2000 Ada GenerationとNVRTC 12.4.127を使用しました。Windowsでは `CUDA_NVRTC_DIR`、インストール済みのPythonパッケージ、`CUDA_PATH/bin` などからNVRTCを探します。Linuxでは `libnvrtc.so.12` と関連ライブラリをシステムローダーまたは `LD_LIBRARY_PATH` で参照可能にしてください。本プロジェクトでの動作確認環境はWindowsです。

## 3オクターブの音階を再生成する

```sh
python src/render_trumpet_bach5c.py
python src/render_trombone_detailed_scale.py
python src/render_trombone_detailed_scale.py --louder
python src/render_trombone_detailed_scale.py --stronger
python src/render_tuba_scale.py
```

WAVと音ごとの測定結果は、上のコマンド順に `output/trumpet_bach5c/`、`output/trombone_detailed_scale/`、`output/trombone_louder_forte/`、`output/trombone_stronger_forte/`、`output/tuba_axisymmetric/` に保存されます。トロンボーンの3つの版をこの順で実行すると、一つ前の版に対する音圧差も計算します。演奏設定には各音の唇の固有振動数、吹奏圧、静止時の唇の開き、運指またはスライド位置、管長補正が含まれます。

まず1音を短く試す場合は、次のコマンドで選んだ音の診断結果を保存できます。音階全体のWAVは上のコマンドで生成します。

```sh
python src/render_trumpet_bach5c.py --only Bb4 --probe 0.45
python src/render_trombone_detailed_scale.py --only Bb3 --probe 0.45
python src/render_tuba_scale.py --only Bb1 --probe 0.45
```

## ユーフォニアム、オフィクレイド、ダブルホルンの音階を再生成する

ユーフォニアムとダブルホルンは実音B♭1〜B♭5、B♭管オフィクレイドは実音B♭1〜B♭4を計算します。オフィクレイドでは運指で開く指穴からの放射、ダブルホルンではF管とB♭管の選択および右手を入れたベルの反射を扱います。

```sh
python src/render_euphonium_ophicleide.py euphonium --extended
python src/render_euphonium_ophicleide.py ophicleide
python src/render_horn_scale.py
```

WAVと各音の測定結果はそれぞれ `output/euphonium_extended/`、`output/ophicleide_axisymmetric/`、`output/horn_axisymmetric/` に保存されます。[ユーフォニアムとオフィクレイドのモデル](docs/ja/EUPHONIUM_OPHICLEIDE_MODEL.md) · [ダブルホルンのモデル](docs/ja/DOUBLE_HORN_MODEL.md)

## フリューゲルホルンとキー付きビューグルの音階を再生成する

実音B♭3〜B♭6をフォルテで、アタックを強めて計算します。ビューグルでは開けた指穴での反射と放射も扱います。実音B♭5を超える7音は、当時の運指表の音域を上に拡張した試算です。

```sh
python src/render_euphonium_ophicleide.py flugelhorn
python src/render_euphonium_ophicleide.py keyed_bugle --no-initial-check
```

WAVと各音の測定結果は `output/flugelhorn_axisymmetric/` と `output/keyed_bugle_axisymmetric/` に保存されます。[管形状、運指と測定結果](docs/ja/FLUGELHORN_KEYED_BUGLE_MODEL.md)

## CPUモデルを実行する

非線形な唇の振動と線形管体を連成したモデルは、次のコマンドで保存済み設定の音階と診断図を生成できます。

```sh
python src/render_scale.py --render
python src/verify.py
```

一次元波動ガイドでは、管内の波が双方向に非線形に伝わり、戻り波が唇に作用します。

```sh
python src/render_bidirectional.py
python src/verify_bidirectional.py
python src/verify_bidirectional.py --full
python src/plot_bidirectional.py
```

入射波を与える非線形伝搬モデルは `python src/render_nonlinear.py` で計算し、`python src/verify_nonlinear.py --full` で検証します。このモデルでは唇による励振を線形共鳴器で求め、その波形を非線形伝搬の入力にします。双方向波動ガイドとCUDAソルバーでは、戻り波も時々刻々の音場から求めます。

## E♭テナーホルンの音階を再生成する

実音B♭2〜B♭5（記譜G3〜G6）をフォルテと強いアタックで計算します。最高4音は通常の演奏域を超えるため、高次の共鳴を使って音域を拡張しています。[モデルと形状データの出典](docs/ja/TENOR_HORN_MODEL.md)

```sh
python src/render_euphonium_ophicleide.py tenor_horn
```

WAVと各音の測定結果は `output/tenor_horn_axisymmetric/` に保存されます。

## モデルと形状

YorkトランペットとConn 8Hの管径は、Campbell、Gilbert、Myersの *The Science of Brass Instruments* に掲載された図から読み取りました。Bach 5Cには公表された実測断面を用い、Denis Wick 5ALはカップ断面を読み取って長さ・容積・単体共鳴から校正しました。BB♭チューバはAlexanderのC管の管径曲線をBB♭管に合わせ、Alexander 163の公称バルブ径とベル径を反映しています。Yamaha BB-67C4は、公開測定値の寸法と容積を基に再構成しました。 [形状データの出典](docs/references.md)

CUDAソルバーは圧縮性Euler方程式に基づき、密度、軸方向と半径方向の運動量、全エネルギーを時間積分します。同心リングの有限体積にMUSCL再構成とHLLC流束を用い、必要に応じてHLLE流束へ切り替えます。時間積分は2段のSSP Runge–Kutta法です。保存形の離散化で衝撃波を扱い、管から戻る音響特性量を用いて唇の流量とカップの圧力を結びます。

3オクターブ版は、円管の周波数依存の粘性・熱損失を考慮します。ベル開口の4モードを等価球の外部音場に結合し、反射波とベル正面1 mの放射音圧を求めます。トランペットでは流れに垂直な向きの唇の復元力に、三次の剛性項も加えています。軸対称化と等価球面は幾何形状の近似です。バルブ通路の曲がり、管壁の振動、乱流ジェット、奏者の声道、室内の反響を扱うには、モデルの拡張が必要です。 [方程式と仮定](docs/models.md) · [楽器ごとの技術ノート](docs/ja/README.md)

## 数値検証

共通のEulerソルバーではSodの衝撃波管、保存性、円筒管の半径方向モードを検証します。ベル外部モデルでは安定性、受動性、相反性を調べ、球面波の反射を別の方法でも計算して比較します。

```sh
python src/verify_axisymmetric.py
python src/verify_bell_exterior.py
```

完成したWAVを別に解析すると、持続部の音程誤差はBach 5Cトランペットで最大約12セント、5ALトロンボーンの3版で最大12セント以内、BB♭チューバで最大約10セントでした。弱い周期変動が見られた音は測定結果に記録しています。数値は再構成した形状と調整済みの演奏設定による合成音の結果です。 [測定と数値検証の一覧](docs/results/README.md)

## リポジトリの構成

| パス | 内容 |
| --- | --- |
| `src/` | シミュレーション、音声生成、検証、作図 |
| `data/` | 管径とマウスピースの形状、演奏設定、出典 |
| `samples/` | 公開WAV、再生成手順、チェックサム |
| `docs/models.md` | 方程式、前提条件、検証範囲 |
| `docs/references.md` | 参考文献と各モデルとの関係 |
| `docs/results/` | 測定結果と数値検証 |
| `docs/figures/` | 診断図 |
| `docs/ja/` | 日本語の技術ノート |
| `output/` | ローカルで生成する音声、時系列、診断結果 |
| `tmp/` | ローカルで生成するキャッシュと作業ファイル |

## 参考文献

形状や音響特性にはCampbell、Gilbert、Myers（2021）、唇の2自由度モデルにはAdachi、Sato（1996）を用いています。人工唇の剛性、円管の粘性・熱損失、ベルの放射には、それぞれの研究を参照しました。書誌情報、図番号、データの利用条件は参考文献に列挙しています。 [参考文献の一覧](docs/references.md)
