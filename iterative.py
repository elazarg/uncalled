#!/usr/bin/python3
from contextlib import contextmanager
from ast import NodeVisitor
import ast
import sys
import glob


class Flags:
    include_strings = True


def is_external_or_in(s):
    def is_external(name):
        prefixes = ['.__', '.test_', '.visit_']
        if any(name.startswith(p) for p in prefixes):
            return True
        return False
    return lambda x: x in s or is_external(x)


class Collector(NodeVisitor):
    @classmethod
    def collect(cls, modules_filenames, referenced=set()):
        collector = cls()
        collector.referenced = is_external_or_in(referenced)
        for module, filename in modules_filenames:
            collector.namespace = ('module ' + filename,)
            collector.visit(module)
        return collector.return_items()

    @contextmanager
    def enter_namespace(self, kind, name):
        self.namespace += ('{} {}'.format(kind, name),)
        yield
        self.namespace = self.namespace[:-1]

    def not_in_class(self):
        return not self.namespace[-1].startswith('class ')

    def visit_ClassDef(self, cd: ast.ClassDef):
        with self.enter_namespace('class', cd.name):
            self.generic_visit(cd)

    def visit_FunctionDef(self, fd: ast.FunctionDef):
        with self.enter_namespace('def', fd.name):
            self.generic_visit(fd)

    def visit_AsyncFunctionDef(self, fd: 'ast.AsyncFunctionDef'):
        return self.visit_FunctionDef(fd)

    def is_referenced(self, name):
        return self.referenced('.' + name) \
            or self.not_in_class() and self.referenced(name)


class Defs(Collector):
    def __init__(self):
        self.defs = {}  # name -> namespace

    def visit_FunctionDef(self, fd: ast.FunctionDef):
        if not self.is_referenced(fd.name):
            self.defs[fd.name] = self.namespace + (str(fd.lineno),)
        super().visit_FunctionDef(fd)

    def return_items(self):
        return self.defs


class Refs(Collector):
    def __init__(self):
        self.refs = set()

    def visit_FunctionDef(self, fd: ast.FunctionDef):
        if self.is_referenced(fd.name) or fd.name in self.refs:
            super().visit_FunctionDef(fd)

    def visit_Attribute(self, attr: ast.Attribute):
        self.refs.add('.' + attr.attr)

    def visit_Name(self, name: ast.Name):
        if isinstance(name.ctx, ast.Load):
            self.refs.add(name.id)

    def visit_Str(self, st: ast.Str):
        if Flags.include_strings:
            self.refs.add(st.s)
            self.refs.add('.' + st.s)

    def return_items(self):
        return self.refs


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


def find_unused(files):
    modules_filenames = tuple(parse_modules(files))
    referenced = set()
    while True:
        now_referenced = Refs.collect(modules_filenames,
                                      referenced=referenced)
        if now_referenced <= referenced:
            break
        referenced.update(now_referenced)
    return Defs.collect(modules_filenames, referenced)


def print_unused(defs):
    for item, (filename, *namespace, line) in sorted(defs.items(), key=lambda x:x[1]):
        path = '.'.join(namespace)
        print('{0}:{1}\t{2}'.format(filename[7:], line, item, path), end=' ')
        if path:
            print('\tat', path, end='')
        print()


def main(files):
    print_unused(find_unused(files))


if __name__ == '__main__':
    main(sys.argv[1:] or glob.glob('*.py'))

def really_unused(): pass
