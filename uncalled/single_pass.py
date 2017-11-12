import os
from .whitelist import get_matcher

is_framework = get_matcher('')


def read_file(filenames):
    for filename in filenames:
        basename = os.path.basename(filename)
        if basename.startswith('.'):
            continue
        if os.path.isfile(filename) and os.path.splitext(filename)[-1] == '.py':
            with open(filename) as f:
                yield (filename, f.read())
        elif os.path.isdir(filename):
            if basename.startswith('__'):
                continue
            yield from read_file([filename + '/' + f for f in os.listdir(filename)])

        
def run(filenames, make_finder):
    file_text = dict(read_file(filenames))
    files = list(file_text.keys())
    finders = {f: make_finder(f, txt) for f, txt in file_text.items()}
    file_defs = {f: finders[f].find_defs() for f, txt in file_text.items()}
    file_uses = {f: finders[f].find_uses() for f, txt in file_text.items()}
    uses = {call for calls in file_uses.values() for call in calls}
    file_unused_defs = {(file, name)
                        for file in files
                        for name in file_defs[file] - uses
                        if not is_framework(name)}
    return file_unused_defs


def report(file_unused_defs):
    for file, name in sorted(file_unused_defs):
        print('{}: Unused function {}'.format(file, name))
