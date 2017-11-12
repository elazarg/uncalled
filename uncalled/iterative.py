#!/usr/bin/python3
from contextlib import contextmanager
from collections import namedtuple
import ast

from . import whitelist
is_framework = whitelist.get_matcher()

# TODO: import as alias, not use


class Kind:
    MODULE = 'module'
    CLASS = 'class'
    FUNC = 'function'
    NAME = 'variable'


Namespace = namedtuple('Namespace', ['kind', 'name', 'lineno'])

    
class Collector(ast.NodeVisitor):
    def __init__(self):
        self.definitions = []  # list(xpath)
        self.references = []  # list(xpath)

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
        name = attr.attr
        value = attr.value
        lineno = attr.lineno
        if isinstance(attr.ctx, ast.Store):
            if isinstance(value, ast.Name) and value.id == 'self':
                namespace = Namespace(Kind.NAME, '.' + name, lineno)
                self.definitions.append(self.xpath[:-1] + (namespace,))
                self.visit(value)
        else:
            self.references.append(self.xpath + (Namespace(Kind.NAME, name, lineno),))
            self.references.append(self.xpath + (Namespace(Kind.NAME, '.' + name, lineno),))
            self.visit(value)

    def visit_Name(self, name: ast.Name):
        id = name.id
        if isinstance(name.ctx, ast.Store):
            with self.enter_definition(Kind.NAME, id, name.lineno):
                pass
        else:
            if self.xpath[-1].kind is Kind.CLASS:
                id = '.' + id
            self.references.append(self.xpath + (Namespace(Kind.NAME, id, name.lineno),))

    # ImportFrom(identifier? module, alias* names, int? level)
    def visit_ImportFrom(self, imp: ast.ImportFrom):
        # TODO: handle aliases
        for alias in imp.names:
            self.references.append((Namespace(Kind.MODULE, imp.module + '.py', imp.lineno),
                                    Namespace(Kind.NAME, alias.name, imp.lineno)))


def collect(filenames):
    c = Collector()
    for module, filename in parse_modules(filenames):
        c.xpath = (Namespace(Kind.MODULE, filename, 0),)
        c.visit(module)
    return c.references, c.definitions


def find_unused(all_references, all_definitions_paths):
    references = set()
    while True:
        new_references = {xpath[-1].name for xpath in all_references
                          if is_reachable(xpath[:-1], references)}
        if new_references <= references:
            break
        references.update(new_references)
        all_references = [xpath for xpath in all_references
                          if xpath[-1].name not in references]
    return {xpath for xpath in all_definitions_paths
            if not is_reachable(xpath, references)}


def is_reachable(xpath, references):
    for (kind, name, _) in xpath:
        if (kind is not Kind.CLASS
            and kind is not Kind.MODULE
                and name not in references
                and not is_framework(name)):
            return False
    return True


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


def print_unused(names):
    for xpath in sorted(names):
        if xpath[-1].kind is Kind.CLASS and not whitelist.Flags.track_classes:
            continue
        if xpath[-1].kind is Kind.NAME and not whitelist.Flags.track_variables:
            continue
        kind, fullname = username_xpath(xpath)
        print("{module.name}:{xpath.lineno}: Unused {kind} '{fullname}'".format(
            module=xpath[0], xpath=xpath[-1], kind=kind, fullname=fullname))


def run(files):
    all_references, all_definitions_paths = collect(files)
    print_unused(find_unused(all_references, all_definitions_paths))
