# NEPP for iPhone

iOS版NEPPは、アプリが前面にある間だけ公開サーバーへ接続し、現在の
Earth Dateを表示するSwiftUIクライアントです。

```text
now:
2026.4320123456
```

## 表示の仕組み

アプリは`nepp.kenic.jp:56377/UDP`へ同期し、受信したEarth Dateと
Earth Date Rateを基準に端末内で連続表示します。表示更新のたびに
ネットワークへ問い合わせるのではなく、約60秒ごとに再同期し、その間は
単調時計を用いて補間します。

- `now:`を約0.01秒周期で更新
- Stratumと最終同期時刻を表示
- 数値をタップすると通常の日時を表示
- 歯車からサーバーとポートを設定
- バックグラウンドでは通信を停止

## 現在の状態

実機iPhoneから公開NEPPサーバーへの通信に成功しています。App Store公開に
向けて、UI、アクセシビリティ、アイコン、TestFlight配布を整備中です。

ソースコードとビルド手順は
[`ios/`](https://github.com/kenic/nepp/tree/main/ios)にあります。

サポートについては[NEPP サポート](support.md)、情報の取り扱いについては
[プライバシーポリシー](privacy.md)をご覧ください。
