from re import findall, IGNORECASE, MULTILINE


class RegexFinder:
    def __init__(self, filename, txt):
        self.txt = txt

    def find_defs(self):
        return set([x.strip()[4:] for x in findall(r'^\s+def [^\d\W]\w*', self.txt, MULTILINE)])

    def find_uses(self):
        return set(findall(r'(?<!def )[^\d\W]\w*', self.txt, IGNORECASE))

    def find_prefixes(self):
        return set(findall(r'''(?<=['"])[a-z_]+(?=['"]\s*[+])''', self.txt, IGNORECASE))

