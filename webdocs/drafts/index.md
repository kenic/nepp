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
| `draft-iwata-nepp-02`（最新草案・V2提案） | [読む](draft-iwata-nepp-02-jp.md) | [Read](draft-iwata-nepp-02.md) | [日本語](source/draft-iwata-nepp-02-jp.txt) · [English](source/draft-iwata-nepp-02.txt) |
| `draft-iwata-nepp-01`（V1仕様） | [読む](draft-iwata-nepp-01-jp.md) | [Read](draft-iwata-nepp-01.md) | [日本語](source/draft-iwata-nepp-01-jp.txt) · [English](source/draft-iwata-nepp-01.txt) |
| `draft-iwata-nepp-00`（過去版） | [読む](draft-iwata-nepp-00-jp.md) | [Read](draft-iwata-nepp-00.md) | [日本語](source/draft-iwata-nepp-00-jp.txt) · [English](source/draft-iwata-nepp-00.txt) |

**英語版が正本で、日本語版は参考資料です。** 内容や解釈に相違がある場合は、
英語版を優先してください。特に`-00`は日英で章構成・収録範囲が異なります。
ダウンロード原稿は提供された内容のまま保存しています。

## 実装との関係

[Version 1実装スナップショット](implementation-snapshot-v1.md)は、
`spec/`にある短い実装概要で、上記`-01`の原稿とは別文書です。

このアーカイブの最新草案は`-02`です。iOSアプリ`0.0.1`が使用するのは
プロトコルVersion 1です。文書の改訂番号、プロトコルの版、アプリの版は別の番号です。

`-02`は太陽位相を追加するV2と関連技術との比較を含む提案です。
V2のパケット配置・天文モデルは未実装・独立検証前であり、現行サービスの変更を意味しません。

## 関連リンク

- [プロトコルの概要](../protocol.md)
- [GitHubリポジトリ](https://github.com/kenic/nepp)
