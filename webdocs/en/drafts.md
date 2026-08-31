# NEPP drafts and revisions

[日本語版](../drafts/index.md){ .md-button }

Each published revision has a permanent URL. Published originals are preserved;
changes will be published as new revisions. The newest draft and the version
supported by an implementation are identified separately.

!!! note "Document status"
    These are author-supplied working drafts. Publication here does not imply
    submission to the IETF, IETF standardization, or approval.

## Available revisions

| Revision | English | 日本語 | Source (Markdown-formatted text) |
|---|---|---|---|
| `draft-iwata-nepp-03` (latest working draft; revised V2 proposal) | [Read](../drafts/draft-iwata-nepp-03.md) | [読む](../drafts/draft-iwata-nepp-03-jp.md) | [English](../drafts/source/draft-iwata-nepp-03.txt) · [日本語](../drafts/source/draft-iwata-nepp-03-jp.txt) |
| `draft-iwata-nepp-02` (historical V2 proposal) | [Read](../drafts/draft-iwata-nepp-02.md) | [読む](../drafts/draft-iwata-nepp-02-jp.md) | [English](../drafts/source/draft-iwata-nepp-02.txt) · [日本語](../drafts/source/draft-iwata-nepp-02-jp.txt) |
| `draft-iwata-nepp-01` (V1 specification) | [Read](../drafts/draft-iwata-nepp-01.md) | [読む](../drafts/draft-iwata-nepp-01-jp.md) | [English](../drafts/source/draft-iwata-nepp-01.txt) · [日本語](../drafts/source/draft-iwata-nepp-01-jp.txt) |
| `draft-iwata-nepp-00` (historical) | [Read](../drafts/draft-iwata-nepp-00.md) | [読む](../drafts/draft-iwata-nepp-00-jp.md) | [English](../drafts/source/draft-iwata-nepp-00.txt) · [日本語](../drafts/source/draft-iwata-nepp-00-jp.txt) |

**The English edition is authoritative; the Japanese edition is for reference only.**
In case of differences in content or interpretation, the English edition takes
precedence. In particular, the `-00` editions differ in structure and coverage.
Downloadable originals are preserved as supplied.

## Implementation status

The [Version 1 implementation snapshot](../drafts/implementation-snapshot-v1.md)
is the shorter overview in `spec/`, a separate document from the `-01` draft above.

The latest working draft in this archive is `-03`. The iOS app `0.0.1`
uses protocol Version 1. Draft revision numbers, protocol versions, and app
versions are independent.

Revision `-03` separates coordinate definitions from their sources, permits
explicitly unassessed ED/SP, and proposes independent quality descriptors.
Its 160-octet V2 layout replaces the unimplemented 128-octet proposal in `-02`;
these experimental V2 layouts are not wire-interoperable. A local experimental
V2-only server now implements the layout and provisional model, with unassessed
accuracy. Independent astronomical validation is pending. Publishing the draft
does not change the deployed V1 service.

V2-only operation is permitted. Continued V1 service and operation of old
clients are not guaranteed after migration; users may need an app update.
V1 support and fallback are optional. Service cutover will be a separate action.

## Related links

- [Protocol overview](protocol.md)
- [GitHub repository](https://github.com/kenic/nepp)
