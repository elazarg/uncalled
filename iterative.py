#!/usr/bin/python3
from contextlib import contextmanager
from collections import namedtuple
from enum import Enum
import ast


# TODO: import as alias, not use

class Flags:
    include_strings = True
    ignore_underscored_methods = False
    ignore_underscored = True
    track_classes = False
    track_variables = False


class Kind(str, Enum):
    MODULE = 'module'
    CLASS = 'class'
    FUNC = 'function'
    NAME = 'variable'


Namespace = namedtuple('Namespace', ['kind', 'name', 'lineno'])

    
class Collector(ast.NodeVisitor):
    def __init__(self):
        self.references =  [] # list(xpath)
        self.definitions = [] # list(xpath)

    def visit_AsyncFunctionDef(self, fd: 'ast.AsyncFunctionDef'):
        return self.visit_FunctionDef(fd)

    def visit_FunctionDef(self, fd: ast.FunctionDef):
        with self.enter_definition(Kind.FUNC, fd.name, fd.lineno):
            self.generic_visit(fd)

    def visit_ClassDef(self, cd: ast.ClassDef):
        with self.enter_definition(Kind.CLASS, cd.name, cd.lineno):
            self.generic_visit(cd)

    @contextmanager
    def enter_definition(self, kind, name, lineno):
        if self.xpath[-1].kind is Kind.CLASS:
            name = '.' + name
        self.xpath += (Namespace(kind, name, lineno),)
        self.definitions.append(self.xpath)
        yield
        self.xpath = self.xpath[:-1]

    def visit_Attribute(self, attr: ast.Attribute):
        node = attr
        name = node.attr
        if isinstance(node.ctx, ast.Store):
            if isinstance(attr.value, ast.Name) and attr.value.id == 'self':
                namespace = Namespace(Kind.NAME, '.' + name, node.lineno)
                self.definitions.append(self.xpath[:-1] + (namespace,))
                self.generic_visit(node)
        else:
            self.references.append(self.xpath + (Namespace(Kind.NAME, name, node.lineno), ))
            self.references.append(self.xpath + (Namespace(Kind.NAME, '.' + name, node.lineno), ))
            self.generic_visit(node)

    def visit_Name(self, name: ast.Name):
        node = name
        name = node.id
        if isinstance(node.ctx, ast.Store):
            with self.enter_definition(Kind.NAME, name, node.lineno):
                self.generic_visit(node)
        else:
            if self.xpath[-1].kind is Kind.CLASS:
                name = '.' + name
            self.references.append(self.xpath + (Namespace(Kind.NAME, name, node.lineno), ))
            self.generic_visit(node)

    @staticmethod
    def collect(modules_filenames):
        self = Collector()
        for module, filename in modules_filenames:
            self.xpath = (Namespace(Kind.MODULE, filename, 0),)
            self.visit(module)
        return self.references, self.definitions


def find_unused(files):
    modules_filenames = tuple(parse_modules(files))
    all_references, all_definitions_paths = Collector.collect(modules_filenames)
    references = set()
    while True:
        new_references = {xpath[-1].name for xpath in all_references
                          if is_reachable(xpath[:-1], references)}
        if new_references <= references:
            break
        references.update(new_references)
    return {xpath for xpath in all_definitions_paths
            if not is_reachable(xpath, references)}


def username_xpath(xpath):
    x1, x2 = xpath[-2], xpath[-1]
    k1, k2 = x1.kind, x2.kind
    if k1 is Kind.CLASS:
        pair = x1.name + x2.name
        if k2 is Kind.CLASS:
            return 'inner class', pair
        if k2 is Kind.FUNC:
            return 'method', pair
        if k2 is Kind.NAME:
            return 'attribute', pair
        else:
            assert False, str(k2)
    if k2 == Kind.NAME:
        return 'variable', x2.name
    if k2 == Kind.FUNC:
        return 'function', x2.name
    if k2 == Kind.CLASS:
        return 'class', x2.name
    assert False, str(x2) 


def is_external(name):
    prefixes = ['.__', '.test_', '.visit_']
    if Flags.ignore_underscored_methods:
        prefixes.append('._')
    if Flags.ignore_underscored:
        prefixes.append('_')
    if any(name.startswith(p) for p in prefixes):
        return True
    return False


def is_reachable(xpath, references):
    return all(is_external(n.name) 
               or n.name in references 
               or n.kind in [Kind.CLASS, Kind.MODULE]
               for n in xpath)


def print_unused(names):
    for xpath in sorted(names):
        kind, fullname = username_xpath(xpath)
        print("{module.name}:{xpath.lineno}: Unused {kind} '{fullname}'".format(
            module=xpath[0], xpath=xpath[-1], kind=kind, fullname=fullname))


def parse_modules(filenames):
    for filename in filenames:
        with open(filename) as f:
            source = f.read()
        try:
            module = ast.parse(source, filename=filename)
        except SyntaxError:
            from sys import stderr
            print('Could not parse ' + filename, file=stderr)
        else:
            yield module, filename


def main(files):
    print_unused(find_unused(files))


if __name__ == '__main__':
    import sys
    import glob
    main(sys.argv[1:] or glob.glob('*.py'))
