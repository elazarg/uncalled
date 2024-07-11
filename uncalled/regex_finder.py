import re
from pathlib import Path

from uncalled.single_pass import Finder


def prepare(txt: str) -> str:
    # this is a hack to remove comments. It may remove too much, but rarely
    txt = re.sub(r"#[^\r\n]*", "", txt)

    return re.sub(r'"""[^\r]*?"""' + r"|'''[^\r]*?'''", "...", txt)


class RegexFinder(Finder):
    def __init__(self, filename: Path, txt: str) -> None:
        super().__init__(filename, txt)
        self.txt = prepare(txt)

    def find_defs(self) -> set[str]:
        return set(
            [
                x.strip()[4:]
                for x in re.findall(r"^\s+def [^\d\W]\w*", self.txt, re.MULTILINE)
            ]
        )

    def find_uses(self) -> set[str]:
        return set(re.findall(r"(?<!def )[^\d\W]\w*", self.txt, re.IGNORECASE))

    def find_prefixes(self) -> set[str]:
        return set(
            re.findall(r"""(?<=['"])[a-z_]+(?=['"]\s*[+])""", self.txt, re.IGNORECASE)
        )
