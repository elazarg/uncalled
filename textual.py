from re import findall, IGNORECASE, MULTILINE

from whitelist import get_matcher
is_framework = get_matcher('')


def find_defs(txt):
    return set([x.strip()[4:] for x in findall('^\s+def [^\d\W]\w*', txt, MULTILINE)])

def find_uses(txt):
    return set(findall('(?<!def )[^\d\W]\w*', txt, IGNORECASE))


def read_file(filename):
    with open(filename) as f:
        return f.read()

        
def main(files):
    files = list(sorted(files))
    file_text = {f: read_file(f) for f in files}
    file_defs = {f: find_defs(txt) for f, txt in file_text.items()}
    file_uses = {f: find_uses(txt) for f, txt in file_text.items()}
    uses = {call for calls in file_uses.values()
             for call in calls}
    file_unused_defs = [(file, name)
                        for file in files
                        for name in file_defs[file] - uses
                            if not is_framework(name)]
    for file, name in file_unused_defs:
        print('{}: Unused function {}'.format(file, name))


if __name__ == '__main__':
    import glob
    import sys
    main(sys.argv[1:] or glob.glob('*.py'))
