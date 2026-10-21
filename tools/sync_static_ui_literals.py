import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "media_sorter.py"
ENGLISH = ROOT / "locales" / "en.json"


def static_ui_literals(source: str) -> set[str]:
    tree = ast.parse(source)
    values: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg in {"text", "label", "title"} and isinstance(keyword.value, ast.Constant):
                value = keyword.value.value
                if isinstance(value, str) and any(character.isalpha() for character in value):
                    values.add(value)
        function_name = node.func.attr if isinstance(node.func, ast.Attribute) else ""
        if function_name in {"askstring", "askinteger", "askfloat"}:
            for argument in node.args[:2]:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    values.add(argument.value)
        if function_name in {"title", "wm_title"} and node.args:
            argument = node.args[0]
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                values.add(argument.value)
    return values


def main() -> None:
    pack = json.loads(ENGLISH.read_text(encoding="utf-8"))
    literals = pack.setdefault("literals", {})
    for value in sorted(static_ui_literals(SOURCE.read_text(encoding="utf-8")), key=str.casefold):
        literals.setdefault(value, value)
    ENGLISH.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
