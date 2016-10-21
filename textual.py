from re import findall, IGNORECASE
import glob
import sys


def find_defs(txt):
    return set([x[5:] for x in findall(' def [a-z][0-9a-z_]+', txt, IGNORECASE)])


def find_calls(txt):
    return set(findall('(?<!def )[a-z][0-9a-z_]+', txt, IGNORECASE))


def main(files):
    file_defs = {}
    calls = set()
    for file in files:
        file_defs[file] = set()
        with open(file) as f:
            text = f.read()
            file_defs[file].update(find_defs(text))
            calls.update(find_calls(text))
    for file in file_defs:
        file_defs[file] = {x for x in file_defs[file] - calls 
                           if 'visit' not in x and not x.startswith('test_')}
        
    for file, defs in file_defs.items():
        if not defs:
            continue
        print(file, ':')
        for d in defs:
            print('\t{}'.format(d))


if __name__ == '__main__':
    main(sys.argv[1:] or glob.glob('*.py'))

