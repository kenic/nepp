# NEPP ドラフト・過去版

[English](../en/drafts.md){ .md-button }

NEPPの仕様原稿を版ごとの固定URLで公開します。掲載済みの原稿は上書きせず、
改訂は新しい版として追加します。最新版の草案と、実装が対応する仕様は区別します。

!!! note "文書の位置づけ"
    著者提供の作業草案を掲載しています。このサイトへの掲載は、IETFへの提出や
    IETFによる標準化・承認を意味しません。

## 掲載版

| 版 | 日本語 | English | 原稿（Markdown形式のテキスト） |
|---|---|---|---|
| `draft-iwata-nepp-03`（最新草案・V2改訂案） | [読む](draft-iwata-nepp-03-jp.md) | [Read](draft-iwata-nepp-03.md) | [日本語](source/draft-iwata-nepp-03-jp.txt) · [English](source/draft-iwata-nepp-03.txt) |
| `draft-iwata-nepp-02`（過去のV2提案） | [読む](draft-iwata-nepp-02-jp.md) | [Read](draft-iwata-nepp-02.md) | [日本語](source/draft-iwata-nepp-02-jp.txt) · [English](source/draft-iwata-nepp-02.txt) |
| `draft-iwata-nepp-01`（V1仕様） | [読む](draft-iwata-nepp-01-jp.md) | [Read](draft-iwata-nepp-01.md) | [日本語](source/draft-iwata-nepp-01-jp.txt) · [English](source/draft-iwata-nepp-01.txt) |
| `draft-iwata-nepp-00`（過去版） | [読む](draft-iwata-nepp-00-jp.md) | [Read](draft-iwata-nepp-00.md) | [日本語](source/draft-iwata-nepp-00-jp.txt) · [English](source/draft-iwata-nepp-00.txt) |

**英語版が正本で、日本語版は参考資料です。** 内容や解釈に相違がある場合は、
英語版を優先してください。特に`-00`は日英で章構成・収録範囲が異なります。
ダウンロード原稿は提供された内容のまま保存しています。

## 実装との関係

[Version 1実装スナップショット](implementation-snapshot-v1.md)は、
`spec/`にある短い実装概要で、上記`-01`の原稿とは別文書です。

このアーカイブの最新草案は`-03`です。iOSアプリ`0.0.1`が使用するのは
プロトコルVersion 1です。文書の改訂番号、プロトコルの版、アプリの版は別の番号です。

`-03`は座標定義と基準源を分離し、ED/SPの精度未評価を明示できるようにして、
座標別品質情報を提案します。160オクテットV2案は`-02`の未実装128オクテット案を
置き換え、両案にワイヤ互換性はありません。ローカルの実験用V2専用サーバーは
パケット配置と暫定天文モデルを実装していますが、誤差未評価・独立天文検証前です。
草案公開は現行V1サービスの変更を意味しません。

V2専用運用を認め、移行後のV1サービス継続・旧クライアントの動作は保証しません。
アプリ更新が必要になる場合があります。V1対応と切り替えは任意で、本番の切り替えは別途行います。

## 関連リンク

- [プロトコルの概要](../protocol.md)
- [GitHubリポジトリ](https://github.com/kenic/nepp)
