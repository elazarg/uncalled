import argparse
from . import single_pass
from . import ast_finder
from . import regex_finder


def main():
    parser = argparse.ArgumentParser(description='Find uncalled function in Python projects')
    parser.add_argument('--how', choices=['ast', 'regex', 'both'], default='regex',
                        help='technique to use. use "both" to reduce false positives [default: regex]')
    parser.add_argument('files', nargs='+', default='.', help='files to analyze')
    args = parser.parse_args()

    results_ast = set()
    if args.how in ['both', 'ast']:
        results_ast = single_pass.run(args.files, ast_finder.AstFinder)
    results_regex = set()
    if args.how in ['both', 'regex']:
        results_regex = single_pass.run(args.files, regex_finder.RegexFinder)
    if args.how == 'both':
        result = results_ast & results_regex
    else:
        result = results_ast | results_regex
    single_pass.report(result)


if __name__ == '__main__':
    main()
