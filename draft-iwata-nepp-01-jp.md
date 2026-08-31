# Network Earth Position Protocol（NEPP）
## 地球公転位置に基づく実数暦の表現および同期プロトコル
### draft-iwata-nepp-01 日本語ドラフト

Internet-Draft  
Intended status: Experimental  
K. Iwata  
Tottori University  
August 2026

---

## 概要

本書は、地球の年周運動に基づく連続的な暦座標「Earth Date」を表現し、ネットワークを通じて同期するための実験的プロトコル、Network Earth Position Protocol（NEPP）を規定する。

従来の民用暦は、地球の自転に由来する「日」を用いて年を構成する。しかし、地球の自転運動と公転運動は互いに独立した天文現象であり、一公転は整数個の自転周期では表せない。このため従来暦では、閏日などの補正を必要とする。

NEPPは、年を整数個の日から構成しない。

NEPPは、地球中心から見た太陽の見かけの方向と国際的な天文標準に基づいてNEPP太陽黄経 λ を定義し、Earth Date（ED）を、

    ED = Y + λ / 360°

として表す。

ここでYはEarth Year、λは0°以上360°未満のNEPP太陽黄経である。

NEPPはさらに、NTPに類似したネットワーク同期機構を定義する。クライアントはNEPPサーバとの4座標交換によって、自身のEarth Date Clockと基準Earth Dateとの差を推定し、同期する。

本版では、draft-iwata-nepp-00で規定した基本概念に加え、Earth Dateの固定小数点表現、NEPP Version 1基本パケット、4座標交換、Earth Date Rate、Stratum、誤差表現、および参照実装に必要な最小限の規則を定義する。

---

# 1. -00からの主な変更点

draft-iwata-nepp-01では、-00から以下を追加または明確化した。

1. NEPP Timestampの96 bit固定小数点表現を規定した。
2. NEPP Version 1基本パケットのバイト配置を規定した。
3. パケットのbyte orderをnetwork byte orderとした。
4. NTP型のOrigin、Receive、Transmit、Destination座標交換を規定した。
5. Earth Date Rateの符号化方式を規定した。
6. Root DelayおよびRoot Dispersionの表現を規定した。
7. Stratum、Status、Mode、Poll、Precisionの意味を規定した。
8. クライアント／サーバの基本動作を規定した。
9. Earth Dateの非等速性を考慮した同期方法を明確化した。
10. 参照天文プロファイルの概念を導入した。
11. 参照実装および相互運用試験に必要なTest Vectorの形式を規定した。

Earth Dateそのものの基本的な天文学的定義は-00から変更しない。

---

# 2. 要求事項を表す用語

英語版におけるMUST、MUST NOT、REQUIRED、SHALL、SHALL NOT、SHOULD、SHOULD NOT、RECOMMENDED、MAY、OPTIONALは、BCP 14のRFC 2119およびRFC 8174に従って解釈する。

---

# 3. Earth Date

## 3.1. 基本定義

Earth Date EDは、

    ED = Y + λ / 360°

と定義する。

ここで、

    Y = Earth Year

    0° ≦ λ < 360°

である。

λはNEPP太陽黄経である。

---

## 3.2. 季節座標

主要な季節点は、

    春分        Y.000000000...
    夏至        Y.250000000...
    秋分        Y.500000000...
    冬至        Y.750000000...
    次の春分    (Y+1).000000000...

に対応する。

これらは角度座標であり、等しい物理時間間隔を意味しない。

---

## 3.3. Earth Year

Earth Year Yは、NEPP太陽黄経が0°となるイベントから始まり、λが一周して次に0°となるまでとする。

初期のNEPPでは、その春分を含むグレゴリオ暦年と同じ整数をYとして使用する。

グレゴリオ暦はEarth Yearの整数ラベルを与えるためだけに使用する。

Earth Dateの小数部分の定義には使用しない。

---

# 4. NEPP太陽黄経

## 4.1. 基準

NEPP太陽黄経は、

    ・太陽の見かけの地心視方向
    ・IAUの黄道定義
    ・IAU 2006歳差モデル
    ・IAU 2000A章動モデル
    ・IERS Conventionsと整合する天文計算

に基づいて求める。

---

## 4.2. 太陽方向

太陽方向は地球中心から見た見かけの方向とする。

単純な二体問題による地球－太陽ベクトルをEarth Dateの定義に用いてはならない。

光行時間、光行差その他、採用する天文標準が要求する補正を適用する。

---

## 4.3. 黄経

太陽の見かけの地心視方向を黄道面へ射影し、春分方向を0°として見かけの太陽年周運動方向に測った角度をλとする。

λは、

    0° ≦ λ < 360°

に正規化する。

---

## 4.4. 円軌道および理想楕円を仮定しない

NEPPは一定角速度の円軌道を仮定しない。

また、理想的な二体ケプラー楕円軌道そのものをEarth Dateの規範的定義とはしない。

Earth Dateは、採用した高精度天体暦および天文標準によって得られる天文状態に従う。

---

# 5. SI時間との関係

## 5.1. SI秒はEarth Dateを定義しない

SI秒はEarth Dateの定義要素ではない。

NEPPは、

    1 Earth Year = N SI seconds

という関係を定義しない。

また、

    ED(t + 1 s) = ED(t) + K

となる普遍的定数Kも定義しない。

---

## 5.2. SI秒の用途

SI秒は、

    ・通信遅延
    ・Poll interval
    ・ローカル発振器の測定
    ・Earth Dateの補間
    ・Earth Dateの予測
    ・holdover
    ・同期誤差の評価

に使用してよい。

---

## 5.3. Earth Date Rate

Earth Date Rate Rを、

    R = dED/dt

とする。

tの単位はSI秒である。

したがってRの単位は、

    ED / SI second

である。

RはEarth Dateを定義する値ではなく、Earth Date Clockが同期点間を補間するための状態量である。

---

# 6. NEPP Timestamp

## 6.1. 形式

NEPP Version 1のEarth Date Timestampは96 bitとする。

    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                      Earth Year                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    +                     Orbital Fraction                          +
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Earth Yearは32 bit符号付き整数とする。

Orbital Fractionは64 bit符号なし整数とする。

---

## 6.2. Orbital Fraction

Earth Dateの小数部分をFとする。

    F = ED - Y
    0 ≦ F < 1

wire上の64 bit値Uは、

    U = floor(F × 2^64)

とする。

受信側は、

    F = U / 2^64

として復元する。

---

## 6.3. Byte Order

NEPP Version 1のすべての複数byte整数はnetwork byte order、すなわちbig endianで送信しなければならない。

---

## 6.4. 年境界

例えば、

    2026.999999...
        ↓
    2027.000000...

という遷移は正常なEarth Date進行である。

Earth Date差を計算する実装は、整数年と小数部分を分離したまま単純減算してはならない。

論理的な実数値、

    Y + U / 2^64

として差を計算しなければならない。

---

# 7. Earth Date Rateのwire表現

Earth Date Rateは64 bit符号付き2の補数整数として送信する。

wire値をSRとすると、

    R = SR × 2^-63 ED/s

と定義する。

すなわち、

    SR = round(R × 2^63)

である。

通常の地球年周運動ではRは正である。

符号付き表現とするのは、演算および将来の拡張を容易にするためである。

---

# 8. NEPP Version 1基本パケット

NEPP Version 1の基本パケット長は76 octetsとする。

すべてのoffsetはpacket先頭から数える。

    Offset   Length   Field
    ------   ------   -------------------------
       0       1      Flags
       1       1      Stratum
       2       1      Poll
       3       1      Precision

       4       4      Root Delay
       8       4      Root Dispersion
      12       4      Reference ID

      16      12      Reference Earth Date
      28      12      Origin Earth Date
      40      12      Receive Earth Date
      52      12      Transmit Earth Date

      64       8      Earth Date Rate
      72       4      Model ID

    Total: 76 octets

76 octets以降には将来のExtension Fieldを配置してよい。

---

# 9. Flags

Flags octetは次の通りとする。

    +---+---+---+---+---+---+---+---+
    | S | S | V | V | V | M | M | M |
    +---+---+---+---+---+---+---+---+

    S = Status Indicator   2 bit
    V = Version Number     3 bit
    M = Mode               3 bit

---

# 10. Status Indicator

Status Indicatorは、

    0    synchronized
    1    degraded astronomical source
    2    prediction-only / holdover
    3    unsynchronized

とする。

このフィールドはNTPのLeap Indicatorと同じbit位置を利用するが、NEPPでは閏秒を表さない。

NEPP Earth Dateには閏秒および閏日は存在しない。

---

# 11. Version

本書で規定するVersion Numberは、

    VN = 1

とする。

---

# 12. Mode

Modeは、

    0    reserved
    1    symmetric active
    2    symmetric passive
    3    client
    4    server
    5    broadcast
    6    reserved
    7    reserved

とする。

Version 1の基本参照実装はMode 3およびMode 4を実装しなければならない。

---

# 13. Stratum

Stratumは参照天文源からの論理的距離を表す。

    0       reference astronomical source
    1       primary NEPP server
    2-15    secondary NEPP server
    16      unsynchronized
    17-255  reserved

Stratum 0は通常、ネットワークサーバそのものを意味しない。

例えば、

    ・高精度太陽系天体暦
    ・公認された天文データ源
    ・基準天文計算系

などをStratum 0 sourceとして扱う。

Stratum 1サーバはStratum 0 sourceから直接Earth Dateを求める。

---

# 14. Poll

Pollは符号付き8 bit整数とする。

推奨同期間隔は、

    2^Poll SI seconds

である。

例えばPoll = 6は約64秒を意味する。

SI秒はここではネットワーク動作間隔を指定するだけであり、Earth Dateを定義しない。

---

# 15. Precision

Precisionは符号付き8 bit整数Pとする。

サーバのEarth Date Clockの公称分解能を、

    2^P ED

として表す。

Pは通常、負の値となる。

---

# 16. Root Delay

Root DelayはNTP short formatと同様の32 bit unsigned 16.16 fixed-point値とする。

単位はSI秒である。

Root Delayは、当該サーバからStratum 1基準源までの累積往復通信遅延の推定値を表す。

---

# 17. Root Dispersion

Root Dispersionは32 bit unsigned 16.16 fixed-point値とする。

単位はSI秒である。

これは当該サーバから基準源までの累積した同期不確かさの上限推定値を表す。

天文モデルそのものの不確かさが無視できない場合、その影響もRoot DispersionまたはExtension Fieldへ反映しなければならない。

---

# 18. Reference ID

Reference IDは32 bitとする。

Stratum 1では使用する天文基準源またはプロファイルを識別する。

上位Stratumでは、同期元NEPP Serverの識別および同期ループ検出に利用してよい。

Version 1ではReference IDの大域的なIANA登録を要求しない。

---

# 19. Model ID

Model IDは32 bitとする。

Model IDは、Earth Dateを算出するために使用した天文実現プロファイルを識別する。

本書では参照プロファイルとして、

    NEPP Astronomical Profile 1

を定義する。

Profile 1は、

    ・高精度太陽系天体暦
    ・IAU 2006 precession
    ・IAU 2000A nutation
    ・IERS Conventionsと整合するapparent geocentric solar direction

を使用する。

Profile 1の厳密なreference procedureとtest vectorはAppendix AおよびBで規定する。

異なる天体暦を用いて、結果の差が公称不確かさ以下である実装は、相互運用上Profile 1互換として扱ってよい。

---

# 20. 4座標同期

## 20.1. イベント

基本的なNEPP request/responseでは、

    E1    Client Transmit Earth Date
    E2    Server Receive Earth Date
    E3    Server Transmit Earth Date
    E4    Client Destination Earth Date

を用いる。

---

## 20.2. Client Request

クライアント要求では、

    Origin Earth Date       = 0
    Receive Earth Date      = 0
    Reference Earth Date    = 任意または0
    Transmit Earth Date     = E1

とする。

---

## 20.3. Server Response

サーバは要求を受信した時点でE2を取得する。

応答では、

    Origin Earth Date       = 要求のTransmit Earth Date
    Receive Earth Date      = E2
    Transmit Earth Date     = E3

とする。

E3は可能な限り実際のpacket送信イベントに近い時点で取得する。

---

## 20.4. Client Destination

クライアントは応答を受けた時点でE4を取得する。

E4はwire上には存在しない。

---

# 21. Earth Date Clock Offset

同期交換が十分短く、Earth Date Rateを一定とみなせる場合、

    θED =
       ((E2 - E1) + (E3 - E4)) / 2

によってクライアントEarth Date Clockのoffsetを推定できる。

θED > 0の場合、クライアントClockはサーバより遅れている。

θED < 0の場合、クライアントClockはサーバより進んでいる。

---

# 22. 非等速性

Earth Dateについて、

    dED/dt ≠ constant

である。

したがって前節の式は数学的には局所近似である。

通常のネットワーク同期のように交換時間が短い場合、Earth Date Rateの変化は十分小さいため、この近似を使用してよい。

要求精度に対して局所線形近似の誤差が無視できない実装は、Earth Date Rateおよび必要に応じて高次の項を用いて、各座標を共通の物理時間基準へ写像してから遅延およびoffsetを推定しなければならない。

---

# 23. Holdover

NEPP Clientは、NEPP Serverとの常時接続を必要としてはならない。

最後の同期点を、

    ED0
    R0

とし、SI時間Δtが経過した場合、短期間では、

    ED ≈ ED0 + R0 Δt

として推定してよい。

より長時間では、

    ED ≈ ED0
         + R0 Δt
         + 1/2 A0 Δt²
         + ...

またはローカル天文モデルを使用することが望ましい。

---

# 24. Clock Discipline

クライアントは繰り返し同期によってEarth Date Clockを補正する。

小さなoffsetは滑らかに補正することが望ましい。

大きなoffsetは即時stepしてもよい。

Earth Date表示は、通常の動作では逆行しないことが望ましい。

---

# 25. 複数サーバ

高信頼性用途では複数のNEPP Serverを使用することが望ましい。

選択には、

    ・Stratum
    ・Root Delay
    ・Root Dispersion
    ・network delay
    ・過去の安定性
    ・Model ID
    ・基準源の独立性

を利用してよい。

明らかに他の高品質な基準源から逸脱したサーバは除外することが望ましい。

---

# 26. UDP Transport

NEPP Version 1の基本transportはUDP request/responseとする。

IANAから正式なport番号が割り当てられるまでは、実験実装はdynamic/private port range内の設定可能なportを使用しなければならない。

実装は特定の暫定port番号をプロトコル仕様として固定してはならない。

---

# 27. セキュリティ

NEPPはNTPと類似する以下の攻撃を受け得る。

    ・応答偽造
    ・server impersonation
    ・replay
    ・delay attack
    ・虚偽のStratum
    ・同期ループ
    ・denial of service

Version 1の基本参照実装は、少なくとも要求と応答の対応関係をOrigin Earth Dateによって検証しなければならない。

高信頼性用途では認証されたtransportまたはNEPP authentication extensionを用いるべきである。

---

# 28. エラー処理

以下の場合、クライアントは応答を同期に使用してはならない。

    ・Versionが未対応
    ・Modeが不正
    ・Statusがunsynchronized
    ・Origin Earth Dateが送信したE1と一致しない
    ・Timestampの符号化が不正
    ・Root Dispersionが実装上の許容値を超える
    ・packet lengthが76 octets未満
    ・reserved valueを不正に使用している

未知のExtension Fieldは、当該Extensionがcriticalとして定義されていない限り無視してよい。

---

# 29. Reference Implementation Requirements

NEPP Version 1の参照サーバは最低限、

    ・Profile 1 Earth Date計算
    ・UDP server mode
    ・E2/E3 timestamp
    ・Earth Date Rate
    ・Stratum
    ・Root Delay
    ・Root Dispersion

を実装しなければならない。

参照クライアントは最低限、

    ・UDP client mode
    ・E1/E4 timestamp
    ・Origin validation
    ・offset計算
    ・Earth Date Clock補正
    ・holdover

を実装しなければならない。

---

# 30. Appendix A
## NEPP Astronomical Profile 1

Profile 1は、NEPP Version 1における参照天文実現である。

Profile 1実装は、

1. 高精度な太陽系天体暦から、指定された天文時刻における地球および太陽の状態を得る。

2. 地球中心から見た太陽の方向を求める。

3. 適用される光伝播および光行差補正を行い、見かけの地心視太陽方向を得る。

4. IAU 2006歳差モデルおよびIAU 2000A章動モデルを適用する。

5. IERS Conventionsと整合する当日黄道および当日赤道を構成する。

6. 春分方向を0°としたNEPP太陽黄経λを求める。

7.

       ED = Y + λ / 360°

   によりEarth Dateを得る。

SOFAと整合するアルゴリズムを参照実装として使用することが望ましい。

NEPPの規範的定義は特定のプログラミング言語またはSOFA関数名そのものには依存しない。

---

# 31. Appendix B
## Test Vectors

相互運用可能性を確認するため、NEPP仕様は以下の形式のTest Vectorを提供する。

各Test Vectorは少なくとも、

    ・天文計算上の入力epoch
    ・Model ID
    ・期待されるNEPP太陽黄経λ
    ・期待されるEarth Year Y
    ・期待される64 bit Orbital Fraction
    ・期待される96 bit Earth Date Timestamp
    ・期待されるEarth Date Rate

を含む。

Test Vectorの例：

    Vector ID: TV-01

    Astronomical profile:
        NEPP Profile 1

    Input epoch:
        [reference astronomical epoch]

    Solar longitude:
        [to be generated from reference implementation]

    Earth Date:
        [to be generated]

    Earth Year bytes:
        xx xx xx xx

    Orbital Fraction bytes:
        xx xx xx xx xx xx xx xx

Test Vectorの具体的な数値は、Profile 1の最初の参照実装から生成し、独立した天文計算との照合後に本ドラフトへ追加する。

数値が確定していないTest Vectorを規範的な適合性試験として使用してはならない。

---

# 32. IANA Considerations

本版ではIANAへの割り当てを要求しない。

将来の版では必要に応じて、

    ・NEPP UDP service port
    ・Model ID registry
    ・Extension Type registry
    ・Reference Source identifier

の登録を要求する可能性がある。

---

# 33. 実装状況

本書執筆時点では、相互運用可能性を確認済みのNEPP Version 1実装は存在しない。

最初の参照実装として、

    nepp-server
    nepp-client

を作成することを想定する。

参照実装の完成後、Appendix BのTest Vectorを生成し、本節を更新する。

---

# 34. 設計原則

NEPPは以下の原則に基づく。

1. 年は整数個の日ではない。

2. Earth Dateは地球の実際の年周天文状態に従う。

3. Earth DateはSI秒の積算によって定義されない。

4. SI秒はEarth Dateの測定、予測、補間、同期に利用できる。

5. Earth Dateの進行速度は一定でなくてよい。

6. 地球自転と地球公転は別の座標として扱う。

7. NEPPはEarth Dateの算出だけでなく、ネットワーク同期を提供する。

8. NTPで実績のある同期モデルは、Earth Dateの性質に適合する範囲でNEPPでも利用する。

9. 地球を暦へ近似するのではなく、暦を地球へ一致させる。

要約すれば、

    地球が暦に従うのではない。

    暦が地球に従う。

---

# 35. References

## Normative References

RFC 2119  
Key words for use in RFCs to Indicate Requirement Levels.

RFC 8174  
Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words.

IAU 2006 Resolution B1  
Adoption of the P03 Precession Theory and Definition of the Ecliptic.

IAU 2000A  
IAU 2000A Nutation Model.

IERS Conventions (2010)  
IERS Technical Note 36.

## Informative References

RFC 5905  
Network Time Protocol Version 4: Protocol and Algorithms Specification.

IAU SOFA  
Standards of Fundamental Astronomy.

---

# 著者

Kenichi Iwata  
Tottori University  
Japan
