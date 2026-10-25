#!/usr/bin/env python3
"""Интерактивное меню генераторов из каталога extra.

Файл находится в extra/extra_launcher.py. Запустите его из корня репозитория:
    python extra/extra_launcher.py

Для выбранного шаблона лаунчер запускает его generator, а при успешном
завершении — соответствующий test_generator. Скрипты ищутся в каталоге
шаблона; для новых генераторов дополнительно поддерживается поиск по имени
файла внутри extra, если структура каталогов отличается.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Parameter:
    name: str
    label: str
    description: str
    aliases: tuple[str, ...] = ()
    kind: str = "text"


@dataclass(frozen=True)
class Template:
    key: str
    title: str
    folder: str
    description: str
    parameters: tuple[Parameter, ...]
    preferred_generator: Optional[str] = None


TEMPLATES: tuple[Template, ...] = (
    Template(
        key="k_m_number",
        title="Перевод числа из k-ричной системы в m-ричную",
        folder="k_m_number",
        description=(
            "Генерирует программу многоленточной машины Тьюринга для перевода "
            "числа между системами счисления. Параметры k и m — основания систем."
        ),
        parameters=(
            Parameter("k", "k", "Исходное основание системы счисления (целое число от 2 до 36).", ("source_base", "from_base", "input_base", "base_k"), "base36"),
            Parameter("m", "m", "Целевое основание системы счисления (целое число от 2 до 36).", ("target_base", "to_base", "output_base", "base_m"), "base36"),
        ),
    ),
    Template(
        key="substring_search",
        title="Поиск заданной подстроки во входной строке",
        folder="substring_search",
        description=(
            "Генерирует программу одноленточной МТ в алфавите {a, b, #}, "
            "которая проверяет, встречается ли заданная подстрока во входной строке."
        ),
        parameters=(
            Parameter("pattern", "pattern", "Непустая искомая подстрока из символов a и b.", ("substring", "needle", "search_string", "sub"), "pattern"),
        ),
    ),
    Template(
        key="db_substring",
        title="Проверка, является ли входная строка подстрокой БД",
        folder="db_substring",
        description=(
            "Генерирует программу одноленточной МТ в алфавите {a, b, #}, "
            "проверяющую, является ли входная строка подстрокой фиксированной строки БД."
        ),
        parameters=(
            Parameter("db", "db", "Строка базы данных — шаблон из символов a и b.", ("database", "base_string", "text", "haystack"), "db"),
        ),
    ),
    Template(
        key="erase_prefix_before_match",
        title="Стирание префикса перед самым левым вхождением подстроки",
        folder="erase_prefix_before_match",
        description=(
            "Генерирует одноленточную МТ для алфавита {a, b, #}. Если шаблон найден, "
            "стирает символы перед самым левым вхождением; если не найден — стирает всё слово."
        ),
        parameters=(
            Parameter("pattern", "pattern", "Непустой шаблон из символов a и b.", ("substring", "needle", "sub"), "pattern"),
        ),
        preferred_generator="erase_prefix_before_match_generator.py",
    ),
    Template(
        key="add_constant",
        title="Прибавление константы к m-ричному числу",
        folder="add_constant",
        description=(
            "Генерирует одноленточную МТ, прибавляющую k к числу в системе основания m. "
            "Ориентация задаёт сторону, на которой находится младший разряд (LSB)."
        ),
        parameters=(
            Parameter("m", "m", "Основание системы счисления (целое число от 2 до 36).", ("base", "base_m"), "base36"),
            Parameter("k", "k", "Неотрицательная константа, которую нужно прибавить.", ("constant", "number"), "nonnegative"),
            Parameter("orientation", "orientation", "Сторона младшего разряда: left или right.", ("lsb", "lsb_side", "direction"), "orientation"),
        ),
        preferred_generator="add_constant_generator.py",
    ),
    Template(
        key="add_number",
        title="Сложение двух чисел в k-ричной системе",
        folder="add_number",
        description=(
            "Генерирует трёхленточную МТ для сложения двух чисел в системе основания k. "
            "Младший разряд записан слева; входные ленты сохраняются, результат записывается на третью."
        ),
        parameters=(
            Parameter("k", "k", "Основание системы счисления (целое число от 2 до 36).", ("base", "base_k"), "base36"),
        ),
        preferred_generator="add_number_generator.py",
    ),
    Template(
        key="reverse_string",
        title="Разворот строки на одноленточной МТ",
        folder="reverse_string",
        description=(
            "Генерирует программу, которая разворачивает слово на ленте: #word# → #reverse(word)#. "
            "Алфавит можно задать компактно (abc) или через запятую (a,b,c)."
        ),
        parameters=(
            Parameter("alphabet", "alphabet", "Непустой алфавит из односимвольных элементов; '#' зарезервирован.", ("symbols", "sigma"), "alphabet"),
        ),
        preferred_generator="reverse_string_generator.py",
    ),
    Template(
        key="validate_number",
        title="Проверка корректности записи числа в системе основания m",
        folder="validate_number",
        description=(
            "Генерирует одноленточную МТ для проверки канонической записи m-ричного числа: "
            "без ведущих нулей, кроме самого числа 0."
        ),
        parameters=(
            Parameter("m", "m", "Основание системы счисления (целое число от 2 до 36).", ("base", "base_m"), "base36"),
            Parameter("orientation", "orientation", "Сторона младшего разряда: left или right.", ("lsb", "lsb_side", "direction"), "orientation"),
        ),
        preferred_generator="validate_number_generator.py",
    ),
)

PARAMETER_ALIASES: dict[str, tuple[str, ...]] = {}
for template in TEMPLATES:
    for parameter in template.parameters:
        existing = PARAMETER_ALIASES.get(parameter.name, ())
        PARAMETER_ALIASES[parameter.name] = tuple(
            dict.fromkeys((*existing, parameter.name, *parameter.aliases))
        )


def normalize_name(value: str) -> str:
    """Нормализует имена CLI-аргументов и файлов для сравнения."""
    return re.sub(r"[^a-z0-9]+", "", value.lower().lstrip("-"))


def repo_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "extra").is_dir():
        return here
    if here.name.lower() == "extra" and here.parent.is_dir():
        return here.parent
    return here


def describe_templates() -> None:
    print("\nДоступные шаблоны\n" + "=" * 78)
    for index, template in enumerate(TEMPLATES, start=1):
        print(f"{index}. {template.title} [{template.key}]")
        print(f"   Каталог: extra/{template.folder}")
        for parameter in template.parameters:
            print(f"   Параметр {parameter.name}: {parameter.description}")
        print(f"   Описание: {template.description}\n")


def choose_template() -> Optional[Template]:
    describe_templates()
    while True:
        choice = input(f"Выберите шаблон (1–{len(TEMPLATES)}, q — выход): ").strip().lower()
        if choice in {"q", "quit", "exit", "выход"}:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(TEMPLATES):
            return TEMPLATES[int(choice) - 1]
        # Also allow selecting by stable key, e.g. add_constant.
        for template in TEMPLATES:
            if choice == template.key:
                return template
        print("Не понял выбор. Введите номер из списка, ключ шаблона или q для выхода.\n")


def parse_alphabet(raw: str) -> list[str]:
    if "," in raw:
        symbols = [part.strip() for part in raw.split(",")]
    else:
        symbols = list(raw)
    if not symbols or any(symbol == "" for symbol in symbols):
        raise ValueError("алфавит должен содержать хотя бы один символ")
    for symbol in symbols:
        if len(symbol) != 1:
            raise ValueError("каждый символ алфавита должен состоять из одного знака")
        if symbol.isspace() or symbol in {"#", ",", ":", "|"}:
            raise ValueError("символы алфавита не могут быть пробелами или #, ',', ':' и '|'")
    if len(set(symbols)) != len(symbols):
        raise ValueError("символы алфавита должны быть различными")
    return symbols


def validate_parameter(parameter: Parameter, value: str) -> Optional[str]:
    if parameter.kind in {"base", "base36", "nonnegative"}:
        try:
            number = int(value)
        except ValueError:
            return "Нужно ввести целое число."
        if parameter.kind in {"base", "base36"} and number < 2:
            return "Основание системы счисления должно быть не меньше 2."
        if parameter.kind in {"base", "base36"} and number > 36:
            return "Поддерживаются основания только от 2 до 36."
        if parameter.kind == "nonnegative" and number < 0:
            return "Значение должно быть неотрицательным."
    elif parameter.kind in {"pattern", "db"}:
        if not value:
            return "Шаблон / строка БД должны быть непустыми."
        invalid = sorted(set(value) - {"a", "b"})
        if invalid:
            return "Допустимы только символы a и b. Недопустимые: " + "".join(invalid)
    elif parameter.kind == "orientation":
        if value.lower() not in {"left", "right"}:
            return "Введите left или right."
    elif parameter.kind == "alphabet":
        try:
            parse_alphabet(value)
        except ValueError as exc:
            return str(exc)
    return None


def collect_parameters(template: Template) -> dict[str, str]:
    values: dict[str, str] = {}
    print("\nВведите параметры (Ctrl+C — отмена):")
    for parameter in template.parameters:
        while True:
            value = input(f"  {parameter.label}: ").strip()
            error = validate_parameter(parameter, value)
            if error:
                print(f"  Ошибка: {error}")
                continue
            # Normalize enumerated parameters; keep strings and alphabet as entered.
            if parameter.kind == "orientation":
                value = value.lower()
            values[parameter.name] = value
            break
    print("\nВыбрано:")
    for parameter in template.parameters:
        print(f"  {parameter.name} = {values[parameter.name]}")
    return values


def _script_files(folder: Path) -> list[Path]:
    return sorted(
        (path for path in folder.rglob("*.py") if path.is_file() and "__pycache__" not in path.parts),
        key=lambda path: (len(path.parts), str(path).lower()),
    )


def _preferred_match(path: Path, preferred: Optional[str]) -> bool:
    if not preferred:
        return False
    wanted = normalize_name(Path(preferred).stem)
    stem = normalize_name(path.stem)
    # Accept names created by downloaders that append a duplicate suffix, e.g. (1).
    return stem == wanted or re.fullmatch(re.escape(wanted) + r"\d+", stem) is not None


def find_script(folder: Path, kind: str, preferred: Optional[str] = None) -> Optional[Path]:
    scripts = _script_files(folder)
    if not scripts:
        return None

    if kind == "generator" and preferred:
        matches = [path for path in scripts if _preferred_match(path, preferred)]
        if matches:
            return matches[0]

    def score(path: Path) -> int:
        stem = normalize_name(path.stem)
        is_test = "test" in stem or "tests" in stem
        if kind == "test":
            if stem in {"testgenerator", "testgen", "generatortest", "generatetests", "testgenerators"}:
                return 120
            if is_test and ("generator" in stem or "generate" in stem):
                return 105
            if stem in {"test", "tests", "generatetest", "testcases"}:
                return 70
            return 0

        if is_test:
            return 0
        if stem in {"generator", "generate", "programgenerator", "generateprogram"}:
            return 120
        if "generator" in stem or "generate" in stem:
            return 100
        return 0

    ranked = [(score(path), path) for path in scripts]
    ranked = [(value, path) for value, path in ranked if value > 0]
    if ranked:
        ranked.sort(key=lambda item: (-item[0], len(item[1].parts), str(item[1]).lower()))
        return ranked[0][1]

    if kind == "generator":
        non_test = [path for path in scripts if not any(token in normalize_name(path.stem) for token in ("test", "tests"))]
        if len(non_test) == 1:
            return non_test[0]
    return None


def find_template_folder(template: Template) -> Optional[Path]:
    extra = repo_root() / "extra"
    expected = extra / template.folder
    if expected.is_dir():
        if find_script(expected, "generator", template.preferred_generator) is not None:
            return expected
        # Preserve the canonical directory even if its generator uses a generic name.
        if template.preferred_generator is None:
            return expected

    if not extra.is_dir():
        return None
    if template.preferred_generator:
        matches = [
            path for path in extra.rglob("*.py")
            if path.is_file() and _preferred_match(path, template.preferred_generator)
            and "__pycache__" not in path.parts
        ]
        if len(matches) == 1:
            return matches[0].parent
        # If there are duplicate matches, prefer a directory named after the template.
        preferred_dirs = [path for path in matches if path.parent.name == template.folder]
        if len(preferred_dirs) == 1:
            return preferred_dirs[0].parent
    return expected if expected.is_dir() else None


class _ArgumentVisitor(ast.NodeVisitor):
    """Извлекает объявления argparse.ArgumentParser.add_argument из кода."""
    def __init__(self) -> None:
        self.arguments: list[dict[str, object]] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "add_argument":
            names = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
            if names:
                dest = None
                for keyword in node.keywords:
                    if keyword.arg == "dest" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                        dest = keyword.value.value
                        break
                options = [name for name in names if name.startswith("-")]
                positional = [name for name in names if not name.startswith("-")]
                if dest:
                    canonical = dest
                elif options:
                    canonical = max(options, key=len).lstrip("-")
                elif positional:
                    canonical = positional[0]
                else:
                    canonical = ""
                self.arguments.append({
                    "names": names,
                    "options": options,
                    "positional": bool(positional and not options),
                    "canonical": canonical,
                })
        self.generic_visit(node)


def parse_argparse_arguments(source: str) -> list[dict[str, object]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = _ArgumentVisitor()
    visitor.visit(tree)
    return visitor.arguments


def match_parameter(argument: dict[str, object], values: dict[str, str]) -> Optional[str]:
    names = list(argument.get("names", []))
    names.append(str(argument.get("canonical", "")))
    normalized = {normalize_name(str(name)) for name in names}
    for key in values:
        aliases = PARAMETER_ALIASES.get(key, (key,))
        if normalized.intersection(normalize_name(alias) for alias in aliases):
            return key
    return None


def infer_invocation(script: Path, parameters: dict[str, str], ordered_names: Iterable[str]) -> tuple[list[str], Optional[str]]:
    """Собирает CLI-аргументы для argparse, sys.argv или input()."""
    try:
        source = script.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        source = ""

    if "argparse" in source:
        definitions = parse_argparse_arguments(source)
        if definitions:
            command_args: list[str] = []
            mapped = 0
            for definition in definitions:
                key = match_parameter(definition, parameters)
                if key is None:
                    continue
                mapped += 1
                if definition["positional"]:
                    command_args.append(parameters[key])
                else:
                    options = list(definition.get("options", []))
                    flag = max(options, key=len) if options else "--" + key.replace("_", "-")
                    command_args.extend([flag, parameters[key]])
            if mapped:
                return command_args, None
        return [item for name in ordered_names for item in (f"--{name.replace('_', '-')}", parameters[name])], None

    if "sys.argv" in source or re.search(r"\bargv\b", source):
        return [parameters[name] for name in ordered_names], None

    if re.search(r"\binput\s*\(", source):
        return [], "\n".join(parameters[name] for name in ordered_names) + "\n"

    return [parameters[name] for name in ordered_names], None


def format_command(command: list[str]) -> str:
    return " ".join(repr(part) if any(ch.isspace() for ch in part) else part for part in command)


def run_script(
    script: Path,
    folder: Path,
    parameters: dict[str, str],
    ordered_names: tuple[str, ...],
    dry_run: bool = False,
) -> int:
    args, stdin_data = infer_invocation(script, parameters, ordered_names)
    relative_script = script.relative_to(folder)
    command = [sys.executable, str(relative_script), *args]
    print(f"\n>>> {script.name}")
    print("Команда:", format_command(command))
    if stdin_data is not None:
        print("Параметры будут переданы через stdin.")
    if dry_run:
        return 0

    try:
        result = subprocess.run(command, cwd=str(folder), input=stdin_data, text=True, check=False)
    except OSError as exc:
        print(f"Не удалось запустить {script}: {exc}")
        return 127
    if result.returncode != 0:
        print(f"Скрипт завершился с кодом {result.returncode}.")
    return result.returncode


def run_template(template: Template, parameters: dict[str, str], dry_run: bool = False) -> int:
    folder = find_template_folder(template)
    if folder is None or not folder.is_dir():
        print(f"Не найдена папка шаблона extra/{template.folder} или генератор {template.preferred_generator!r}.")
        print("Убедитесь, что extra_launcher.py находится в каталоге extra/ или в корне репозитория.")
        return 2

    generator = find_script(folder, "generator", template.preferred_generator)
    test_generator = find_script(folder, "test")
    if generator is None:
        available = ", ".join(str(path.relative_to(folder)) for path in _script_files(folder)) or "Python-файлов не найдено"
        print(f"Не удалось найти generator в {folder}.")
        print("Найденные файлы:", available)
        return 2

    print(f"\nШаблон: {template.title}")
    print(f"Папка: {folder}")
    code = run_script(generator, folder, parameters, tuple(parameter.name for parameter in template.parameters), dry_run)
    if code != 0:
        print("Проверка тестов не запускается, потому что генератор завершился с ошибкой.")
        return code

    if test_generator is None:
        print("\nПредупреждение: test_generator не найден — запущен только генератор программы.")
        return 0
    return run_script(test_generator, folder, parameters, tuple(parameter.name for parameter in template.parameters), dry_run)


def main() -> int:
    parser = argparse.ArgumentParser(description="Меню генераторов из папки extra.")
    parser.add_argument("--list", action="store_true", help="показать список шаблонов и завершить работу")
    parser.add_argument("--dry-run", action="store_true", help="показать команды, не запуская скрипты")
    args = parser.parse_args()

    if args.list:
        describe_templates()
        return 0

    try:
        template = choose_template()
        if template is None:
            print("Выход.")
            return 0
        values = collect_parameters(template)
        return run_template(template, values, dry_run=args.dry_run)
    except (KeyboardInterrupt, EOFError):
        print("\nОтменено пользователем.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
