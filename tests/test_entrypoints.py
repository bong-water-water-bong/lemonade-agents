"""Smoke tests for packaged Lemonade agent entry points."""

from __future__ import annotations

from importlib.metadata import entry_points


def test_all_department_console_scripts_are_declared() -> None:
    scripts = {entry.name: entry.value for entry in entry_points(group="console_scripts")}

    expected = {
        "lemonade-helper": "lemonade_agents.helper.agent:main",
        "lemonade-cashier": "lemonade_agents.cashier.agent:main",
        "lemonade-inventory": "lemonade_agents.inventory.agent:main",
        "lemonade-accounting": "lemonade_agents.accounting.agent:main",
        "lemonade-marketeer": "lemonade_agents.marketeer.agent:main",
        "lemonade-supplier": "lemonade_agents.supplier.agent:main",
        "lemonade-reports": "lemonade_agents.reports.agent:main",
        "lemonade-security": "lemonade_agents.security.agent:main",
        "lemonade-serve": "lemonade_agents.web.app:main",
    }

    for name, target in expected.items():
        assert scripts[name] == target


def test_all_gaia_agent_entry_points_are_declared() -> None:
    agents = {entry.name: entry.value for entry in entry_points(group="gaia.agents")}

    expected = {
        "lemonade-helper": "lemonade_agents.helper.agent:LemonadeHelperAgent",
        "lemonade-cashier": "lemonade_agents.cashier.agent:CashierAgent",
        "lemonade-inventory": "lemonade_agents.inventory.agent:InventoryAgent",
        "lemonade-accounting": "lemonade_agents.accounting.agent:AccountingAgent",
        "lemonade-marketeer": "lemonade_agents.marketeer.agent:MarketerAgent",
        "lemonade-supplier": "lemonade_agents.supplier.agent:SupplierAgent",
        "lemonade-reports": "lemonade_agents.reports.agent:ReportsAgent",
        "lemonade-security": "lemonade_agents.security.agent:SecurityAgent",
    }

    for name, target in expected.items():
        assert agents[name] == target


def test_package_imports() -> None:
    import lemonade_agents

    assert lemonade_agents.__version__ == "0.1.0"
