# NEPP

<p class="lead">ひとつの惑星。ひとつの連続した日付。</p>

<div class="earth-date" aria-label="NEPP Earth Date example">
  <span>now:</span>
  <strong>2026.4320</strong>
</div>

**Network Earth Position Protocol（NEPP）**は、地球の一年における位置を
連続した実数の日付として表し、ネットワークで交換するための実験的な暦と
同期プロトコルです。

通常の暦が「年・月・日・時・分・秒」という複数の単位で現在を表すのに対し、
NEPPのEarth Dateは一つの数で表します。

```text
2026.4320
```

整数部はEarth Year、小数部はその年の軌道上での位置です。Earth Yearは
3月分点から始まり、太陽の見かけの黄経が一周すると次の年になります。

## すでに動いています

アプリをインストールせず、ブラウザだけでEarth Dateと現在地のSolar Phaseを
確認できます。位置情報は端末内でのみ使用され、NEPPサーバーには送信されません。

[NEPP Webを開く](https://nepp.kenic.jp/web/){ .md-button .md-button--primary }

公開NEPPサーバーは次のアドレスで稼働しています。

```text
nepp.kenic.jp:56377/UDP
```

Pythonの参照クライアントとiPhoneアプリから、同じEarth Dateを取得できます。
サーバー、プロトコル実装、仕様書、iOSクライアントはすべて
[GitHub](https://github.com/kenic/nepp)で公開しています。

## 読む

- [暦](calendar.md) — Earth Dateという表現の考え方
- [プロトコル](protocol.md) — UDPパケットと同期計算
- [iPhoneアプリ](app.md) — 手のひらで動くNEPPクライアント

!!! warning "Experimental"
    NEPP Version 1は実験的なプロトコルです。法定時刻、航法、金融取引、
    安全性が重要な同期には使用できません。

[Read in English](en/index.md){ .md-button }
