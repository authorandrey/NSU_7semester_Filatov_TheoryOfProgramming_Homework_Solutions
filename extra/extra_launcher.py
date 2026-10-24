#!/usr/bin/env python3
"""Интерактивный запуск генераторов из папки extra репозитория.

Положите этот файл в корень репозитория рядом с папкой extra и запустите:
    python extra_launcher.py

Launcher ищет скрипты внутри каждой папки шаблона. Сначала запускается генератор
программы, затем (если найден) test_generator. Поддерживаются аргументы командной
строки, описанные через argparse, позиционные параметры через sys.argv и ввод через
input(). Никакие команды не запускаются через shell.
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


# Пути и описания соответствуют разделу extra в README репозитория.
@dataclass(frozen=True)
class Parameter:
    name: str
    label: str
    description: str
    aliases: tuple[str, ...] = ()
    kind: str = "text"  # "text" or "base"


@dataclass(frozen=True)
class Template:
    key: str
    title: str
    folder: str
    description: str
    parameters: tuple[Parameter, ...]


TEMPLATES: tuple[Template, ...] = (
    Template(
        key="k_m_number",
        title="Перевод числа из k-ричной системы в m-ричную",
        folder="k_m_number",
        description=(
            "Генерирует программу многоленточной машины Тьюринга для перевода "
            "числа между системами счисления. Основания задаются параметрами k и m."
        ),
        parameters=(
            Parameter("k", "k", "Исходное основание системы счисления (целое число ≥ 2).", ("k", "source_base", "from_base", "input_base", "base_k"), "base"),
            Parameter("m", "m", "Целевое основание системы счисления (целое число ≥ 2).", ("m", "target_base", "to_base", "output_base", "base_m"), "base"),
        ),
    ),
    Template(
        key="substring_search",
        title="Поиск заданной подстроки во входной строке",
        folder="substring_search",
        description=(
            "Генерирует программу одноленточной МТ в алфавите {a, b, #}, "
            "проверяющую, встречается ли заданный шаблон во входной строке."
        ),
        parameters=(
            Parameter("pattern", "pattern", "Искомая непустая подстрока из символов a и b.", ("pattern", "substring", "needle", "search_string", "sub")),
        ),
    ),
    Template(
        key="db_substring",
        title="Проверка, является ли входная строка подстрокой БД",
        folder="db_substring",
        description=(
            "Генерирует программу одноленточной МТ в алфавите {a, b, #}, "
            "проверяющую, является ли входная строка подстрокой заранее заданной БД."
        ),
        parameters=(
            Parameter("db", "db", "Строка базы данных — шаблон программы (символы a и b).", ("db", "database", "base_string", "text", "haystack")),
        ),
    ),
)


# Имена аргументов, встречающиеся в разных вариантах CLI.
PARAMETER_ALIASES: dict[str, tuple[str, ...]] = {
    parameter.name: tuple(dict.fromkeys((parameter.name, *parameter.aliases)))
    for template in TEMPLATES
    for parameter in template.parameters
}


def normalize_name(value: str) -> str:
    """Приводит имя CLI-аргумента к виду, удобному для сопоставления."""
    return re.sub(r"[^a-z0-9]+", "", value.lower().lstrip("-"))


def repo_root() -> Path:
    """Поддерживает размещение файла и в корне репозитория, и внутри extra."""
    here = Path(__file__).resolve().parent
    if (here / "extra").is_dir():
        return here
    if here.name == "extra" and here.parent.is_dir():
        return here.parent
    return here


def describe_templates() -> None:
    print("\nДоступные шаблоны\n" + "=" * 72)
    for index, template in enumerate(TEMPLATES, start=1):
        params = ", ".join(
            f"{p.name} — {p.description}" for p in template.parameters
        ) or "нет"
        print(f"{index}. {template.title}")
        print(f"   Папка: extra/{template.folder}")
        print(f"   Параметры: {params}")
        print(f"   Описание: {template.description}\n")


def choose_template() -> Optional[Template]:
    describe_templates()
    while True:
        choice = input(f"Выберите шаблон (1–{len(TEMPLATES)}, q — выход): ").strip().lower()
        if choice in {"q", "quit", "exit", "выход"}:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(TEMPLATES):
            return TEMPLATES[int(choice) - 1]
        print("Не понял выбор. Введите номер из списка или q для выхода.\n")


def validate_parameter(parameter: Parameter, value: str) -> Optional[str]:
    if parameter.kind == "base":
        try:
            base = int(value)
        except ValueError:
            return "Нужно ввести целое число."
        if base < 2:
            return "Основание системы счисления должно быть не меньше 2."
    elif parameter.name == "pattern":
        if not value:
            return "Подстрока должна быть непустой."
        invalid = sorted(set(value) - {"a", "b"})
        if invalid:
            return "Допустимы только символы a и b. Недопустимые символы: " + "".join(invalid)
    elif parameter.name == "db":
        invalid = sorted(set(value) - {"a", "b"})
        if invalid:
            return "Для БД допустимы только символы a и b. Недопустимые символы: " + "".join(invalid)
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
            values[parameter.name] = value
            break
    print("\nВыбрано:")
    for parameter in template.parameters:
        print(f"  {parameter.name} = {values[parameter.name]}")
    return values


def _script_files(folder: Path) -> list[Path]:
    """Python-файлы в папке шаблона, включая вложенные каталоги."""
    return sorted(
        (p for p in folder.rglob("*.py") if p.is_file() and "__pycache__" not in p.parts),
        key=lambda p: (len(p.parts), str(p).lower()),
    )


def find_script(folder: Path, kind: str) -> Optional[Path]:
    """Находит generator/test_generator по имени; поддерживает несколько вариантов названий."""
    scripts = _script_files(folder)
    if not scripts:
        return None

    def score(path: Path) -> int:
        stem = normalize_name(path.stem)
        is_test = "test" in stem or "tests" in stem
        is_generator = "generator" in stem or "generate" in stem or "gen" == stem

        if kind == "test":
            if stem in {"testgenerator", "testgen", "generatortest", "generatetests", "testgenerators"}:
                return 120
            if is_test and is_generator:
                return 105
            if stem in {"test", "tests", "generate_test", "test_cases"}:
                return 70
            return 0

        # Для генератора программы исключаем test_generator.
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

    # Если имя нестандартное, но есть только один скрипт, его можно считать генератором.
    if kind == "generator":
        non_test = [p for p in scripts if not any(token in normalize_name(p.stem) for token in ("test", "tests"))]
        if len(non_test) == 1:
            return non_test[0]
    return None


class _ArgumentVisitor(ast.NodeVisitor):
    """Собирает объявления argparse.ArgumentParser.add_argument в порядке исходника."""

    def __init__(self) -> None:
        self.arguments: list[dict[str, object]] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 - имя AST-метода
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
                # Явный dest важнее имени флага.
                if dest:
                    canonical = dest
                elif options:
                    canonical = max(options, key=len).lstrip("-")
                elif positional:
                    canonical = positional[0]
                else:
                    canonical = ""
                self.arguments.append({"names": names, "options": options, "positional": bool(positional and not options), "canonical": canonical})
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
    """Возвращает ключ параметра, которому соответствует объявление argparse."""
    names = list(argument.get("names", []))
    names.append(str(argument.get("canonical", "")))
    normalized = {normalize_name(str(name)) for name in names}
    for key in values:
        aliases = PARAMETER_ALIASES.get(key, (key,))
        if normalized.intersection(normalize_name(alias) for alias in aliases):
            return key
    return None


def infer_invocation(script: Path, parameters: dict[str, str], ordered_names: Iterable[str]) -> tuple[list[str], Optional[str]]:
    """Строит CLI-аргументы и, если нужно, stdin для скрипта.

    Сначала учитывает объявления argparse. Иначе передаёт параметры позиционно,
    если скрипт использует sys.argv; если виден input() без sys.argv — через stdin.
    """
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
                    # Предпочитаем длинный флаг, например --pattern вместо -p.
                    flag = max(options, key=len) if options else "--" + key.replace("_", "-")
                    command_args.extend([flag, parameters[key]])
            if mapped:
                return command_args, None
        # argparse присутствует, но имена параметров не удалось извлечь.
        return [item for name in ordered_names for item in (f"--{name.replace('_', '-')}", parameters[name])], None

    if "sys.argv" in source or re.search(r"\bargv\b", source):
        return [parameters[name] for name in ordered_names], None

    # Некоторые простые генераторы запрашивают параметры через input().
    if re.search(r"\binput\s*\(", source):
        return [], "\n".join(parameters[name] for name in ordered_names) + "\n"

    # Последний fallback — позиционные аргументы. Если интерфейс скрипта другой,
    # команда будет показана пользователю, а ошибка дочернего скрипта не замалчивается.
    return [parameters[name] for name in ordered_names], None


def format_command(command: list[str]) -> str:
    """Человекочитаемый вид команды (для отчёта; запуск идёт без shell)."""
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
        result = subprocess.run(
            command,
            cwd=str(folder),
            input=stdin_data,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"Не удалось запустить {script}: {exc}")
        return 127

    if result.returncode != 0:
        print(f"Скрипт завершился с кодом {result.returncode}.")
    return result.returncode


def run_template(template: Template, parameters: dict[str, str], dry_run: bool = False) -> int:
    folder = repo_root() / "extra" / template.folder
    if not folder.is_dir():
        print(f"Не найдена папка шаблона: {folder}")
        print("Положите extra_launcher.py в корень репозитория рядом с папкой extra.")
        return 2

    generator = find_script(folder, "generator")
    test_generator = find_script(folder, "test")
    if generator is None:
        available = ", ".join(str(p.relative_to(folder)) for p in _script_files(folder)) or "Python-файлов не найдено"
        print(f"Не удалось найти generator в {folder}.")
        print("Найденные файлы:", available)
        print("Ожидается Python-скрипт, название которого содержит generator/generate, либо единственный .py-файл.")
        return 2

    print(f"\nШаблон: {template.title}")
    print(f"Папка: {folder}")
    code = run_script(generator, folder, parameters, tuple(p.name for p in template.parameters), dry_run)
    if code != 0:
        print("Проверка тестов не запускается, потому что генератор завершился с ошибкой.")
        return code

    if test_generator is None:
        print("\nПредупреждение: test_generator не найден — запущен только генератор программы.")
        return 0

    return run_script(test_generator, folder, parameters, tuple(p.name for p in template.parameters), dry_run)


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
