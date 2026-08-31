"""Publish original drafts separately from the implementation snapshot."""

from pathlib import Path

from mkdocs.structure.files import File


def on_files(files, config):
    root = Path(config.config_file_path).parent
    sources = sorted(root.glob("draft-iwata-nepp-[0-9][0-9].md"))
    sources += sorted(root.glob("draft-iwata-nepp-[0-9][0-9]-jp.md"))
    for source in sources:
        japanese = source.stem.endswith("-jp")
        counterpart = (source.stem[:-3] if japanese else source.stem + "-jp") + ".md"
        links = []
        if (root / counterpart).is_file():
            label = "English" if japanese else "日本語版"
            links.append(f"[{label}]({counterpart}){{ .md-button }}")
        links.append(f"[Source / 原稿](source/{source.stem}.txt){{ .md-button }}")
        links.append("[Archive / 版一覧](index.md)")
        notice = ""
        if japanese:
            notice = (
                '!!! note "日本語版について"\n'
                f"    [英語版]({counterpart})が正本です。この日本語版は参考資料であり、\n"
                "    英語版と内容・構成が異なる場合があります。解釈や仕様に相違がある場合は、\n"
                "    英語版を優先してください。ダウンロード原稿は提供時のまま保存しています。\n\n"
            )
        page = "\n\n".join(links) + "\n\n" + notice + "---\n\n" + source.read_text(encoding="utf-8")
        files.append(File.generated(
            config, f"drafts/{source.name}", content=page
        ))
        files.append(File.generated(
            config, f"drafts/source/{source.stem}.txt", content=source.read_bytes()
        ))
    snapshot = root / "spec" / "draft-iwata-nepp-01.md"
    files.append(File.generated(
        config, "drafts/implementation-snapshot-v1.md",
        abs_src_path=str(snapshot.resolve())
    ))
    return files
