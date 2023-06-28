import re


def prepare(txt: str) -> str:
    return re.sub(r'"""[^\r]*?"""' + r"|'''[^\r]*?'''", '...', txt)


class RegexFinder:
    def __init__(self, filename, txt):
        self.txt = prepare(txt)

    def find_defs(self):
        return set([x.strip()[4:] for x in re.findall(r'^\s+def [^\d\W]\w*', self.txt, re.MULTILINE)])

    def find_uses(self):
        return set(re.findall(r'(?<!def )[^\d\W]\w*', self.txt, re.IGNORECASE))

    def find_prefixes(self):
        return set(re.findall(r'''(?<=['"])[a-z_]+(?=['"]\s*[+])''', self.txt, re.IGNORECASE))
