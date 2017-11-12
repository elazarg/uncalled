from re import findall, IGNORECASE, MULTILINE


class RegexFinder:
    def __init__(self, filename, txt):
        self.txt = txt

    def find_defs(self):
        return set([x.strip()[4:] for x in findall('^\s+def [^\d\W]\w*', self.txt, MULTILINE)])

    def find_uses(self):
        return set(findall('(?<!def )[^\d\W]\w*', self.txt, IGNORECASE))
