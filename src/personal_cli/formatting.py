from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from personal_cli.client import CLIError


def read_markdown_from_source(
    *,
    markdown: str | None,
    markdown_file: Path | None,
) -> str:
    if markdown is not None and markdown_file is not None:
        raise CLIError("Use either --markdown or --markdown-file, not both.")
    if markdown is not None:
        return markdown
    if markdown_file is not None:
        return markdown_file.read_text(encoding="utf-8")
    if sys.stdin.isatty():
        raise CLIError("Provide markdown via --markdown, --markdown-file, or stdin.")
    return sys.stdin.read()


def emit_result(data: Any, *, json_output: bool = False) -> None:
    if json_output:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return

    if isinstance(data, list):
        for item in data:
            print(item)
        return

    print(data)

