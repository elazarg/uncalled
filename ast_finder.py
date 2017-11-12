import ast


class AstFinder:
    def __init__(self, filename, txt):
        self.collector = StoreLoadCollector()
        try:
            parsed = ast.parse(txt)
            self.collector.generic_visit(parsed)
        except SyntaxError:
            # raise SyntaxError('Cannot parse ' + filename) from None
            print('Note: cannot parse ast of ', filename)
            pass

    def find_defs(self):
        return set(self.collector.definitions)

    def find_uses(self):
        return set(self.collector.references)

    
class StoreLoadCollector(ast.NodeVisitor):
    def __init__(self):
        self.definitions = []  # list[str]
        self.references = []  # list[str]

    def visit_AsyncFunctionDef(self, fd: 'ast.AsyncFunctionDef'):
        self.visit_FunctionDef(fd)

    def visit_FunctionDef(self, fd: ast.FunctionDef):
        self.definitions.append(fd.name)
        self.generic_visit(fd)

    def visit_Attribute(self, attr: ast.Attribute):
        if isinstance(attr.ctx, ast.Store):
            pass
        else:
            self.references.append(attr.attr)
        self.generic_visit(attr.value)

    def visit_Name(self, name: ast.Name):
        if isinstance(name.ctx, ast.Store):
            pass
        else:
            self.references.append(name.id)

    def visit_Str(self, s: ast.Str):
        self.references.append(s.s)
