import os
import typing
from pathlib import Path
from typing import Iterable, Iterator

from uncalled.whitelist import get_matcher

is_framework = get_matcher("")


class Finder(typing.Protocol):
    def __init__(self, filename: Path, txt: str) -> None: ...
    def find_defs(self) -> set[str]: ...

    def find_uses(self) -> set[str]: ...

    def find_prefixes(self) -> set[str]: ...


def is_venv(filename: Path) -> bool:
    basename = os.path.basename(filename)
    return basename in ["venv", ".venv", "virtualenv", ".virtualenv"]


def read_file(paths: Iterable[Path]) -> Iterator[tuple[Path, str]]:
    for path in paths:
        basename = path.name
        if basename.startswith("."):
            continue
        if path.is_file() and path.suffix == ".py":
            with open(path, encoding="utf-8") as f:
                yield (path, f.read())
        elif path.is_dir():
            if basename.startswith("__"):
                continue
            if is_venv(path):
                continue
            yield from read_file([path / f for f in os.listdir(path)])


def run(
    filenames: Iterable[str], make_finder: typing.Callable[[Path, str], Finder]
) -> set[tuple[Path, str]]:
    # normalize filenames
    file_paths = [Path(f) for f in filenames]
    file_text = dict(read_file(file_paths))
    files = list(file_text.keys())
    finders = {f: make_finder(f, txt) for f, txt in file_text.items()}
    file_defs = {f: finders[f].find_defs() for f, txt in file_text.items()}
    file_uses = {f: finders[f].find_uses() for f, txt in file_text.items()}
    file_pref = {f: finders[f].find_prefixes() for f, txt in file_text.items()}
    prefs = [p for f, prefs in file_pref.items() for p in prefs]
    uses = {call for calls in file_uses.values() for call in calls}
    file_unused_defs = {
        (file, name)
        for file in files
        for name in file_defs[file] - uses
        if not is_framework(name) and not any(name.startswith(p) for p in prefs)
    }
    return file_unused_defs


def report(file_unused_defs: set[tuple[Path, str]]) -> None:
    for file, name in sorted(file_unused_defs):
        print("{}: Unused function {}".format(file, name))
