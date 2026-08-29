# Network Earth Position Protocol

NEPP Version 1は、NTPに着想を得たUDPリクエスト／レスポンス型の実験的な
同期プロトコルです。公開サーバーは未割当のプライベートポート`56377/UDP`を
使用しています。

## 試す

参照実装をインストールした端末から実行します。

```bash
nepp-client nepp.kenic.jp --port 56377
```

応答例：

```text
earth_date=2026.431818261511104238
offset_ed=5.499863888505608E-9
round_trip_ed=1.3356719301708866E-8
stratum=1
model_id=1
```

## Version 1パケット

基本パケットは76オクテットです。

| Offset | Size | Field |
|---:|---:|---|
| 0 | 1 | Status、Version、Mode |
| 1 | 1 | Stratum |
| 4 | 4 | Root Delay |
| 8 | 4 | Root Dispersion |
| 16 | 12 | Reference Earth Date |
| 28 | 12 | Origin Earth Date |
| 40 | 12 | Receive Earth Date |
| 52 | 12 | Transmit Earth Date |
| 64 | 8 | Earth Date Rate |
| 72 | 4 | Model ID |

Earth Dateの時刻印は、符号付き32ビットのEarth Yearと、符号なし64ビットの
軌道小数部から構成されます。すべてネットワークバイトオーダーです。

## 交換と補正

クライアント送信、サーバー受信、サーバー送信、クライアント受信をそれぞれ
`E1`〜`E4`として、オフセットと往復時間を計算します。

```text
offset = ((E2 - E1) + (E3 - E4)) / 2
round_trip = (E4 - E1) - (E3 - E2)
```

完全な実装スナップショットは
[`draft-iwata-nepp-01`](https://github.com/kenic/nepp/blob/main/spec/draft-iwata-nepp-01.md)
を参照してください。

## セキュリティ

Version 1は認証を備えておらず、偽装、再送、遅延操作、偽のStratum、DoSの
影響を受けます。Origin照合は応答を対応付けますが、送信者を認証しません。
信頼が必要な用途には、認証されたトランスポートまたは将来の拡張が必要です。
