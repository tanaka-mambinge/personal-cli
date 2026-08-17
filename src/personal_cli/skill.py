from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

SKILL_NAME = "content-pipeline"


def skill_install_path(target_dir: Path | None = None) -> Path:
    base = target_dir if target_dir is not None else Path.home() / ".agents" / "skills"
    return Path(base) / SKILL_NAME


def _skill_data_root() -> Path:
    return Path(resources.files("personal_cli")) / "skill_data"


def install_skill(target_dir: Path | None = None) -> Path:
    destination = skill_install_path(target_dir)
    source = _skill_data_root()
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    return destination


def uninstall_skill(target_dir: Path | None = None) -> bool:
    destination = skill_install_path(target_dir)
    if destination.exists():
        shutil.rmtree(destination)
        return True
    return False
