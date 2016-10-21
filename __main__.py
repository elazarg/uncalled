from sys import argv
from glob import glob


if __name__ == '__main__':
    if argv[1] == '--iterative':
        import iterative as target
        files = argv[2:]
    else:
        import textual as target
        files = argv[1:]
    target.main(files or glob('*.py'))
