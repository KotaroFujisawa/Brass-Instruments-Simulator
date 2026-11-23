# E♭テナーホルン（アルトホルン）のモデル

トロンボーンと同じ実音B♭2〜B♭5のB♭メジャー上行音階を、A4 = 440 Hz、フォルテ、強いアタックで計算します。各音は静止した状態から発音し、22音を順につなぎます。音の長さは各1.08秒、最後のB♭5のみ1.65秒、各音の後ろに90 msの無音を入れます。WAVの長さは26.31秒で、48 kHz・16 bit・モノラルです。[トロンボーンのモデル](TROMBONE_MODEL.md) · [演奏プリセット](../../data/performance_tenor_horn.json)

## 管体とマウスピース

管体の基準はAdolphe Sax製の1855年のE♭テナー・サクソルン（Edinburgh University Collection、EU4543）です。*The Science of Brass Instruments* の図7.24がこの個体を示し、図7.26から管路に沿った内径を開口手前の1.89 mまで読み取りました。ベル末端はベッセル曲線で延長し、現代の別個体を参照して管体長2.030 m、ベル径210 mmと仮定しました。マウスピース装着後の開放流路は2.087 mです。教科書表7.1の等価円錐長2.22 mは、E♭2の基準周波数77.8 Hzに対応する半波長です。[教科書第7章](https://doi.org/10.1007/978-3-030-55686-0_7) · [EU4543の収蔵一覧](https://www.euchmi.ed.ac.uk/ubl/ublh09.html) · [図7.26の管径データ](../../data/tenor_horn_sax_eu4543_fig7_26.csv)

開放管体の強奏時の高調波増加の目安として、教科書の式 (6.7) に従い管径分布から `brassiness potential` を求めると約0.59です。Mitrouliaが同じEU4543の採寸から求めた値は0.57です。[教科書第6章](https://doi.org/10.1007/978-3-030-55686-0_6) · [Mitrouliaの採寸資料（付録C）](https://era.ed.ac.uk/items/7ac2fa2c-9867-40b5-a2b4-ca917ea9712e)

マウスピースはヤマハAH-38D4の公称リム内径18.90 mm、スロート径5.25 mm、やや深めのカップを参考に再構成しました。カップ深さ25.5 mm、マウスピース全長75 mm、差し込み長18 mmとし、未公表のカップ内壁とバックボアには推定した軸対称断面を使います。現代のヤマハYAH-803SはE♭管、3ピストン、ボア径11.9 mm、ベル径210 mmで、このAH-38D4を標準付属品としています。[ヤマハの楽器仕様](https://dk.yamaha.com/en/musical-instruments/brass-woodwinds/products/altohorns/yah-803s/specs.html) · [ヤマハのマウスピース仕様](https://au.yamaha.com/en/musical-instruments/brass-woodwinds/products/mouthpieces/altohorns/index.html) · [再構成したマウスピース断面](../../data/yamaha_ah38d4_reconstructed.csv)

## 運指と発音域

E♭テナーホルンはト音記号で記譜し、実音は記譜より長6度低くなります。記譜C4は実音E♭3に対応します。今回の音階は記譜G3〜G6のGメジャーに相当し、ト音記号の3ピストン金管の運指を基準に、必要に応じて別の共鳴を使う替え指を選びます。第1・第2・第3ピストンはそれぞれ2・1・3半音に相当する迂回管長をバルブ区間に加えます。複数を押すと各延長の和を取り、音ごとの有効管長補正も同じ区間に加えます。[ヤマハのテナーホルン解説](https://au.yamaha.com/en/education/greatstart/articles/ensemble-learning/e-flat.html) · [ヤマハの運指表](https://www.yamaha.com/en/musical_instrument_guide/trumpet/play/play002.html) · [演奏プリセット](../../data/performance_tenor_horn.json)

Nigel Horneの編曲ガイドが示す通常の記譜域はF♯3〜C6（実音A2〜E♭5）で、上限を超える発音は奏者の技量に依存します。今回の実音F5・G5・A5・B♭5は計算上の拡張音域です。最低域の実音B♭2・C3も、同ガイドが音程を上ずらせやすいと指摘する記譜B♭3未満に入ります。音階は、各音で唇の固有周波数や吹奏圧などを調整した条件で計算します。[Nigel Horne, *How to Write for Brass Bands*](https://www.ibew.org.uk/dvarch/DV01458.pdf)

## 管内伝搬とベル放射

管の中心線を展開し、軸方向と半径方向を持つ軸対称格子で圧縮性Euler方程式を解きます。有限体積法の流束はMUSCL再構成とHLLC法を用い、必要な箇所ではHLLE法に切り替えます。強奏で起こる波形の急峻化を扱い、壁面の熱粘性損失も近似します。非線形に変形した反射波がマウスピース圧を通じてAdachi–Satoの2自由度唇モデルを駆動し、唇を通る流量が次の音場を変えます。[軸対称ソルバー](AXISYMMETRIC_MODEL.md) · [Adachi–Satoの唇モデル](https://doi.org/10.1121/1.414601)

ベル開口には等価球を使った多モードの放射負荷を与え、ベル面上の半径方向の速度分布から、軸上1 mでの放射音圧を求めます。Roti Rotiは別個体のC. G. Conn製E♭アルトホルンで、ベル面直近の圧力と粒子速度が面内で変化することを測定しています。Ogilvieの2025年の研究には、1988年のBoosey & Hawkes製E♭テナーホルン（開放時の管長約2.03 m、Denis Wick 3）の管径分布と入力インピーダンスの実測があり、現代の同種楽器の比較資料になります。[ベルの放射モデル](../trumpet_bell_exterior.md) · [Roti Rotiのベル近傍測定](https://courses.physics.illinois.edu/phys406/sp2017/NSF_REU_Reports/2014_REU/Annelise_Roti_Roti_Final_REU_Paper.pdf) · [Ogilvieの測定（図4.2a・5.7）](https://www.researchgate.net/publication/395028157_Numerical_Modelling_of_Brasswind_Instrument_Input_Impedance_with_Radiation_and_Viscothermal_Effects)

## 計算結果

定常吹奏圧は音に応じて3.65〜11.20 kPaに設定し、アタックでは最大16.24 kPaまで上げました。書き出したWAVを再解析した結果、22音の持続部で平均律に対する最大音程誤差は9.9セントでした。立ち上がりの音圧が持続部のRMS値の半分に達し、12 ms以上維持するまでの時間は音の開始から20〜46 ms（中央値30 ms）でした。

ベルの軸上1 mでの持続部の放射音圧はモデル上で0.46〜3.18 Pa RMSでした。出力PCMのクリッピングは0サンプルです。

## 再計算

NVIDIA GPUとNVRTCを利用できる環境で、リポジトリのルートから実行します。[実行環境の準備](../../README.md#インストール)

```sh
python src/render_euphonium_ophicleide.py tenor_horn
```

WAVと各音の測定結果は `output/tenor_horn_axisymmetric/` に保存されます。WAVには音階全体で共通のゲインを使い、音圧の比較には `measurements.json` に記録されたゲイン適用前の放射音圧を使います。
