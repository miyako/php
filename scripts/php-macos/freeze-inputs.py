#!/usr/bin/env python3
"""Include rebuild recipes and remove transient state before freezing sources."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys


def main():
    root = Path(sys.argv[1]).resolve()
    scripts = Path(__file__).resolve().parent
    repository = scripts.parents[1]
    destination = root / "runtime-build/scripts/php-macos"
    shutil.copytree(scripts, destination, ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
    shutil.copy2(repository / "LICENSE", root / "runtime-build/LICENSE")
    shutil.copytree(
        repository / ".github/actions/php-macos-tools",
        root / "runtime-build/.github/actions/php-macos-tools", dirs_exist_ok=True,
    )
    bridge = root / "runtime-build/php/Resources/php"
    bridge.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repository / "php/Resources/php/_4D_Execute_PHP.php", bridge)
    (root / ".spc.cache.php").unlink(missing_ok=True)
    logs = root / "log"
    if logs.exists():
        shutil.rmtree(logs)
    tokens = [
        os.environ[name].encode() for name in ("GITHUB_TOKEN", "SPC_GITHUB_TOKEN", "GH_TOKEN")
        if os.environ.get(name)
    ]
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink() and tokens:
            content = path.read_bytes()
            if any(token in content for token in tokens):
                raise RuntimeError(f"Refusing to archive a build credential in {path.relative_to(root)}")
    spec = importlib.util.spec_from_file_location("snapshot", scripts / "snapshot.py")
    snapshot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshot)
    (root / "input-manifest.json").write_text(
        json.dumps(snapshot.inventory(root), indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
