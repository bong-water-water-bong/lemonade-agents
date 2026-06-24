"""Smoke tests for the Lemonade agents package."""

from __future__ import annotations


def test_package_imports_without_optional_web_dependencies() -> None:
    import lemonade_agents

    assert lemonade_agents.__version__ == "0.1.0"
