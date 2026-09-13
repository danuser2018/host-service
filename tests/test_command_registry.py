import pytest
import os
from src.services.command_registry import CommandRegistry, InvalidCatalogError
from src.models.commands import HostCommand, RiskLevel


def test_load_valid_catalog(tmp_path):
    catalog_content = """
commands:
  - name: calculator
    command:
      - gnome-calculator
    risk: low
    phrases:
      - calculadora
      - maquina de calcular
  - name: backup
    command:
      - /usr/local/bin/nova-backup
      - --quick
    risk: medium
    phrases:
      - copia de seguridad
      - hacer backup
  - name: format-disk
    command:
      - /usr/local/bin/nova-format-disk
    risk: high
    phrases:
      - formatear disco externo
"""
    file_path = tmp_path / "commands.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    registry.load_from_file(str(file_path))

    commands = registry.list_all()
    assert len(commands) == 3
    calc = registry.get("calculator")
    assert calc is not None
    assert calc.name == "calculator"
    assert calc.command == ["gnome-calculator"]
    assert calc.risk == RiskLevel.LOW
    assert calc.phrases == ["calculadora", "maquina de calcular"]


def test_load_missing_file_fails():
    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="not found"):
        registry.load_from_file("config/non_existent_file.yaml")


def test_load_corrupted_yaml_fails(tmp_path):
    file_path = tmp_path / "corrupted.yaml"
    file_path.write_text("commands:\n  - name: [invalid yaml syntax:::", encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Error parsing YAML"):
        registry.load_from_file(str(file_path))


def test_load_invalid_root_structure_fails(tmp_path):
    file_path = tmp_path / "invalid_root.yaml"
    file_path.write_text("some_key:\n  - item: 1\n", encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Root must contain 'commands' key"):
        registry.load_from_file(str(file_path))


def test_load_empty_commands_list_fails(tmp_path):
    file_path = tmp_path / "empty_commands.yaml"
    file_path.write_text("commands: []\n", encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="must be a non-empty list"):
        registry.load_from_file(str(file_path))


def test_load_duplicate_names_fails(tmp_path):
    catalog_content = """
commands:
  - name: editor
    command: ["gedit"]
    risk: low
    phrases: ["abrir gedit"]
  - name: editor
    command: ["nano"]
    risk: low
    phrases: ["abrir nano"]
"""
    file_path = tmp_path / "duplicate.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Duplicate command identifier 'editor'"):
        registry.load_from_file(str(file_path))


def test_load_empty_argv_fails(tmp_path):
    catalog_content = """
commands:
  - name: broken
    command: []
    risk: low
    phrases: ["broken"]
"""
    file_path = tmp_path / "empty_argv.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Validation error for command 'broken'"):
        registry.load_from_file(str(file_path))


def test_load_blank_string_argv_fails(tmp_path):
    catalog_content = """
commands:
  - name: broken
    command: [""]
    risk: low
    phrases: ["broken"]
"""
    file_path = tmp_path / "blank_argv.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Validation error for command 'broken'"):
        registry.load_from_file(str(file_path))


def test_load_missing_phrases_fails(tmp_path):
    catalog_content = """
commands:
  - name: broken
    command: ["ls"]
    risk: low
"""
    file_path = tmp_path / "missing_phrases.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Validation error for command 'broken'"):
        registry.load_from_file(str(file_path))


def test_load_empty_phrases_fails(tmp_path):
    catalog_content = """
commands:
  - name: broken
    command: ["ls"]
    risk: low
    phrases: []
"""
    file_path = tmp_path / "empty_phrases.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Validation error for command 'broken'"):
        registry.load_from_file(str(file_path))


def test_load_blank_phrases_fails(tmp_path):
    catalog_content = """
commands:
  - name: broken
    command: ["ls"]
    risk: low
    phrases: ["   ", ""]
"""
    file_path = tmp_path / "blank_phrases.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Validation error for command 'broken'"):
        registry.load_from_file(str(file_path))


def test_load_cleans_phrases_whitespace(tmp_path):
    catalog_content = """
commands:
  - name: calc
    command: ["gnome-calculator"]
    risk: low
    phrases:
      - "  calculadora  "
      - " maquina de calcular "
"""
    file_path = tmp_path / "clean_phrases.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    registry.load_from_file(str(file_path))
    calc = registry.get("calc")
    assert calc.phrases == ["calculadora", "maquina de calcular"]


def test_load_invalid_risk_fails(tmp_path):
    catalog_content = """
commands:
  - name: dangerous
    command: ["rm", "-rf"]
    risk: critical
    phrases: ["destruir todo"]
"""
    file_path = tmp_path / "invalid_risk.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    with pytest.raises(InvalidCatalogError, match="Validation error for command 'dangerous'"):
        registry.load_from_file(str(file_path))


def test_get_existing_command(tmp_path):
    catalog_content = """
commands:
  - name: browser
    command: ["firefox"]
    risk: medium
    phrases: ["abrir navegador"]
"""
    file_path = tmp_path / "browser.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    registry.load_from_file(str(file_path))

    cmd = registry.get("browser")
    assert cmd is not None
    assert cmd.name == "browser"
    assert cmd.command == ["firefox"]
    assert cmd.risk == RiskLevel.MEDIUM
    assert cmd.phrases == ["abrir navegador"]


def test_get_unknown_command(tmp_path):
    catalog_content = """
commands:
  - name: browser
    command: ["firefox"]
    risk: medium
    phrases: ["abrir navegador"]
"""
    file_path = tmp_path / "browser.yaml"
    file_path.write_text(catalog_content, encoding="utf-8")

    registry = CommandRegistry()
    registry.load_from_file(str(file_path))

    assert registry.get("nonexistent") is None
