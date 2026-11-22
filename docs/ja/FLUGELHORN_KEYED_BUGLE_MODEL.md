# フリューゲルホルンと7キー付きビューグルのモデル

両楽器でトランペットの試算と同じ実音B♭3〜B♭6のB♭メジャー上行音階を計算します。A4 = 440 Hz、フォルテでアタックを強めた設定です。全22音を静止状態から個別に計算してつなぎ、各音は1.08秒、最後のB♭6は1.65秒、各音の後ろの無音は90 msです。WAVは26.31秒、48 kHz・16 bit・モノラルです。

## 管体と運指

管径の起点は *The Science of Brass Instruments* の図7.20です。図は各個体の内径を流路に沿って示しており、太いベル末端は省略されています。終端の形状とマウスピースは、後述の寸法を使って再構成しました。[教科書第7章](https://doi.org/10.1007/978-3-030-55686-0_7)

フリューゲルホルンの管体はČervený製のB♭管（EU3664、1900年頃）です。開放時の管体長1,340 mmと、ベル径139 mmを採用します。マウスピースはヤマハFH-11F4を参考にUカップを再構成し、リム内径16.46 mm、スロート径3.80 mm、推定カップ深さ22.5 mmとしました。各バルブを押すと対応する迂回管の長さを加えます。この音階では第1〜第3バルブを使います。[EU3664の収蔵記録](https://mimo-international.com/MIMO/doc/IFD/MINIM_UK_UEDIN_3664) · [Arnold Myersの楽器寸法資料](https://era.ed.ac.uk/server/api/core/bitstreams/2a943b41-3bb4-4f23-82eb-bcd61e984d3b/content) · [ヤマハFH-11F4の仕様](https://jp.yamaha.com/products/musical_instruments/winds/mouthpieces/flugelhorns/additional_tab3434.html) · [図7.20の管径データ](../../data/flugelhorn_cerveny_eu3664_fig7_20.csv) · [演奏プリセット](../../data/performance_flugelhorn.json)

キー付きビューグルの管体はHalari製の7キーC管（EU907、1830年頃）です。Harperの教則本が記す全音下げの替え管でB♭に合わせる構成を使います。指穴はベル側から1〜7番とし、1番は通常開、それ以外は通常閉です。押鍵に応じて開閉が切り替わり、演奏プリセットには実際に開いている穴を記録します。実音B♭5を超える7音は、同時代の7キー運指表より上の音域を計算するための拡張です。[EU907の収蔵記録](https://www.euchmi.ed.ac.uk/ubl/ublh07.html) · [Harperの教則本・運指表](https://www.open-access.bcu.ac.uk/7212/2/Appendices.pdf) · [Eliasonの資料とDodworthの運指表](https://www.govinfo.gov/content/pkg/GOVPUB-SI-PURL-gpo20850/pdf/GOVPUB-SI-PURL-gpo20850.pdf) · [演奏プリセット](../../data/performance_keyed_bugle.json)

ビューグルのHalari製本体長は1,205 mmとし、同時代の英製7キーC管（NMM 06872）のベル径148 mmと実測孔寸法を採用しました。マウスピースはBCUの漏斗形標本13.3の寸法に合わせ、孔のチムニー高は3.2〜4.5 mmと仮定しました。基準となるB♭用替え管は約160.6 mmで、各音の有効管長補正も演奏プリセットに記録します。[7孔とベルの実測寸法](https://emuseum.nmmusd.org/objects/9093/keyed-bugle-c) · [マウスピースの所蔵記録](https://www.bcu.ac.uk/conservatoire/research/hic/the-collection/mouthpieces/13-3) · [B♭用替え管のある現存例](https://www.si.edu/object/firth-hall-pond-7-keyed-bugle%3Anmah_606351)

## 管内伝搬と放射

管の中心線を展開し、管径を保った軸対称の格子上で圧縮性Euler方程式を解きます。流束はMUSCL再構成とHLLC法を用い、必要な箇所ではHLLE法に切り替えます。管内から戻る波がAdachi–Satoの2自由度唇モデルを駆動し、唇の体積流量が次の管内音場を変えます。熱粘性損失を壁面モデルで近似し、ベルの境界には等価球による多モードの放射と反射を用います。[軸対称ソルバー](AXISYMMETRIC_MODEL.md) · [ベルの放射モデル](../trumpet_bell_exterior.md) · [Adachi–Satoの唇モデル](https://doi.org/10.1121/1.414601)

ビューグルの開孔は、管の途中に接続したチムニーと周波数依存の放射で表します。開孔からの反射も唇に戻ります。ベル軸上1 mの計算音には、ベルからの放射と各開孔からの放射を加えます。曲管の立体形状と開孔の外側で起こる音響的な相互作用は軸対称化で省略しています。[側孔の境界モデル](EUPHONIUM_OPHICLEIDE_MODEL.md#管内の連成と放射)

## 出力WAVの測定結果

| 楽器 | 持続部の最大音程差 | 持続部の半分の音圧に達した時刻の中央値 |
| --- | --- | --- |
| フリューゲルホルン | 13.5セント | 24.9 ms |
| キー付きビューグル | 12.8セント | 27.5 ms |

両方のWAVで22音と各音後の90 msの無音区間を確認し、クリッピングは0サンプルでした。ビューグルの19音で開孔からの放射を確認しました。フリューゲルホルンのE♭4とG5、ビューグルのE♭6・F6・G6・A6には弱い多周期変調が見られます。音程は放射波形中で優勢な周期を測っています。

## 再計算

NVIDIA GPUとNVRTCを利用できる環境で、リポジトリのルートから実行します。[実行環境の準備](../../README.md#インストール)

```sh
python src/render_euphonium_ophicleide.py flugelhorn
python src/render_euphonium_ophicleide.py keyed_bugle --no-initial-check
```

WAVと各音の測定結果は、それぞれ `output/flugelhorn_axisymmetric/` と `output/keyed_bugle_axisymmetric/` に保存されます。WAVは楽器ごとに一つの出力ゲインを使います。ビューグルのコマンドでは全音を予定の長さまで進め、放射音の持続部から音程を判定します。
