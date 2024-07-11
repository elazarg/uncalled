from typing import Iterator, Iterable, TypeAlias
from contextlib import contextmanager
import ast
from dataclasses import dataclass

from uncalled import whitelist

is_framework = whitelist.get_matcher()


# TODO: import as alias, not use


class Kind:
    MODULE = "module"
    CLASS = "class"
    FUNC = "function"
    NAME = "variable"


@dataclass(frozen=True)
class Namespace:
    kind: str
    name: str
    lineno: int


XPath: TypeAlias = tuple[Namespace, ...]


class Collector(ast.NodeVisitor):
    xpath: XPath
    definitions: list[XPath]
    references: list[XPath]

    def __init__(self) -> None:
        self.definitions = []
        self.references = []

    def visit_AsyncFunctionDef(self, fd: ast.AsyncFunctionDef):
        with self.enter_definition(Kind.FUNC, fd.name, fd.lineno):
            self.generic_visit(fd)

    def visit_FunctionDef(self, fd: ast.FunctionDef | ast.AsyncFunctionDef):
        with self.enter_definition(Kind.FUNC, fd.name, fd.lineno):
            self.generic_visit(fd)

    def visit_ClassDef(self, cd: ast.ClassDef):
        with self.enter_definition(Kind.CLASS, cd.name, cd.lineno):
            self.generic_visit(cd)

    @contextmanager
    def enter_definition(self, kind, name, lineno) -> Iterator[None]:
        if self.xpath[-1].kind is Kind.CLASS:
            name = "." + name
        self.xpath += (Namespace(kind, name, lineno),)
        self.definitions.append(self.xpath)
        yield
        self.xpath = self.xpath[:-1]

    def visit_Attribute(self, attr: ast.Attribute) -> None:
        name = attr.attr
        value = attr.value
        lineno = attr.lineno
        if isinstance(attr.ctx, ast.Store):
            if isinstance(value, ast.Name) and value.id == "self":
                namespace = Namespace(Kind.NAME, "." + name, lineno)
                self.definitions.append(self.xpath[:-1] + (namespace,))
                self.visit(value)
        else:
            self.references.append(self.xpath + (Namespace(Kind.NAME, name, lineno),))
            self.references.append(
                self.xpath + (Namespace(Kind.NAME, "." + name, lineno),)
            )
            self.visit(value)

    def visit_Name(self, name: ast.Name) -> None:
        id = name.id
        if isinstance(name.ctx, ast.Store):
            with self.enter_definition(Kind.NAME, id, name.lineno):
                pass
        else:
            if self.xpath[-1].kind is Kind.CLASS:
                id = "." + id
            self.references.append(
                self.xpath + (Namespace(Kind.NAME, id, name.lineno),)
            )

    # ImportFrom(identifier? module, alias* names, int? level)
    def visit_ImportFrom(self, imp: ast.ImportFrom) -> None:
        # TODO: handle aliases
        for alias in imp.names:
            if imp.module is None:
                self.references.append(
                    (
                        Namespace(Kind.MODULE, alias.name, imp.lineno),
                        Namespace(Kind.NAME, alias.name, imp.lineno),
                    )
                )
            else:
                self.references.append(
                    (
                        Namespace(Kind.MODULE, imp.module + ".py", imp.lineno),
                        Namespace(Kind.NAME, alias.name, imp.lineno),
                    )
                )


def collect(filenames: Iterable[str]) -> tuple[list, list]:
    c = Collector()
    for module, filename in parse_modules(filenames):
        c.xpath = (Namespace(Kind.MODULE, filename, 0),)
        c.visit(module)
    return c.references, c.definitions


def find_unused(
    all_references: list[XPath], all_definitions_paths: list[XPath]
) -> set[XPath]:
    references = set[str]()
    while True:
        new_references = {
            xpath[-1].name
            for xpath in all_references
            if is_reachable(xpath[:-1], references)
        }
        if new_references <= references:
            break
        references.update(new_references)
        all_references = [
            xpath for xpath in all_references if xpath[-1].name not in references
        ]
    return {
        xpath for xpath in all_definitions_paths if not is_reachable(xpath, references)
    }


def is_reachable(xpath: XPath, references: set[str]) -> bool:
    for item in xpath:
        if (
            item.kind is not Kind.CLASS
            and item.kind is not Kind.MODULE
            and item.name not in references
            and not is_framework(item.name)
        ):
            return False
    return True


def username_xpath(xpath: XPath) -> tuple[str, str]:
    x1, x2 = xpath[-2], xpath[-1]
    k1, k2 = x1.kind, x2.kind
    if k1 is Kind.CLASS:
        pair = x1.name + x2.name
        if k2 is Kind.CLASS:
            return "inner class", pair
        if k2 is Kind.FUNC:
            return "method", pair
        if k2 is Kind.NAME:
            return "attribute", pair
        else:
            assert False, str(k2)
    if k2 == Kind.NAME:
        return "variable", x2.name
    if k2 == Kind.FUNC:
        return "function", x2.name
    if k2 == Kind.CLASS:
        return "class", x2.name
    assert False, str(x2)


def parse_modules(filenames: Iterable[str]) -> Iterator[tuple[ast.Module, str]]:
    for filename in filenames:
        with open(filename, encoding="utf-8") as f:
            source = f.read()
        try:
            module = ast.parse(source, filename=filename)
        except SyntaxError:
            from sys import stderr

            print("Could not parse " + filename, file=stderr)
        else:
            yield module, filename


def print_unused(names: set[XPath]) -> None:
    for xpath in sorted(names):
        if xpath[-1].kind is Kind.CLASS and not whitelist.Flags.track_classes:
            continue
        if xpath[-1].kind is Kind.NAME and not whitelist.Flags.track_variables:
            continue
        kind, fullname = username_xpath(xpath)
        module, *_, file = xpath
        print(f"{module.name}:{file.lineno}: Unused {kind} '{fullname}'")


def run(files: Iterable[str]) -> None:
    all_references, all_definitions_paths = collect(files)
    print_unused(find_unused(all_references, all_definitions_paths))
