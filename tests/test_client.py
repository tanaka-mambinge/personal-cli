from __future__ import annotations

from personal_cli.formatting import read_markdown_from_source


def test_read_markdown_from_source_prefers_inline_text() -> None:
    assert read_markdown_from_source(markdown="hello", markdown_file=None) == "hello"

