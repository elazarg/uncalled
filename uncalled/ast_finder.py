import ast
import sys
from pathlib import Path

from uncalled.single_pass import Finder


class AstFinder(Finder):
    def __init__(self, filename: Path, txt: str) -> None:
        super().__init__(filename, txt)
        self.collector = StoreLoadCollector()
        try:
            parsed = ast.parse(txt)
            self.collector.generic_visit(parsed)
        except SyntaxError:
            print("Note: cannot parse ast of ", filename, file=sys.stderr)
            pass

    def find_defs(self) -> set[str]:
        return set(self.collector.definitions)

    def find_uses(self) -> set[str]:
        return set(self.collector.references)

    def find_prefixes(self) -> set[str]:
        return set()


class StoreLoadCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.definitions: list[str] = []
        self.references: list[str] = []

    def visit_AsyncFunctionDef(self, fd: ast.AsyncFunctionDef) -> None:
        self.definitions.append(fd.name)
        self.generic_visit(fd)

    def visit_FunctionDef(self, fd: ast.FunctionDef) -> None:
        self.definitions.append(fd.name)
        self.generic_visit(fd)

    def visit_Attribute(self, attr: ast.Attribute) -> None:
        if isinstance(attr.ctx, ast.Store):
            pass
        else:
            self.references.append(attr.attr)
        self.generic_visit(attr.value)

    def visit_Name(self, name: ast.Name) -> None:
        if isinstance(name.ctx, ast.Store):
            pass
        else:
            self.references.append(name.id)

    def visit_Str(self, s: ast.Str) -> None:
        self.references.append(s.s)
