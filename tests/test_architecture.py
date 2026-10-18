"""
Архитектурный тест: service.py не должен импортировать fastapi и sqlalchemy
(и вообще любые инфраструктурные модули). Проверка выполняется разбором AST,
поэтому не требует установленных фреймворков.
"""
import ast
import pathlib
import unittest

MODULES = pathlib.Path(__file__).resolve().parents[1] / "app" / "modules"
FORBIDDEN = {"fastapi", "sqlalchemy", "starlette", "app.models", "app.database"}
REFACTORED = ["orders", "users"]


def imported_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class LayerBoundariesTests(unittest.TestCase):
    def test_service_has_no_framework_imports(self):
        for module in REFACTORED:
            names = imported_names(MODULES / module / "service.py")
            for name in names:
                root = name.split(".")[0]
                self.assertNotIn(root, {"fastapi", "sqlalchemy", "starlette"}, f"{module}: {name}")
                self.assertNotIn(name, FORBIDDEN, f"{module}: {name}")

    def test_service_does_not_import_repository(self):
        for module in REFACTORED:
            names = imported_names(MODULES / module / "service.py")
            self.assertFalse(
                any(n.endswith(".repository") for n in names),
                f"{module}: service зависит от конкретного репозитория",
            )

    def test_router_has_no_orm_access(self):
        for module in REFACTORED:
            names = imported_names(MODULES / module / "router.py")
            self.assertNotIn("app.models", names, module)

    def test_three_files_exist(self):
        for module in REFACTORED:
            for f in ("router.py", "service.py", "repository.py"):
                self.assertTrue((MODULES / module / f).exists(), f"{module}/{f}")


if __name__ == "__main__":
    unittest.main()
