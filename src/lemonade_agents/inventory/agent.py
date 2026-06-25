# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Inventory Agent — stock levels, product catalog, low-stock alerts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY
from gaia.agents.chat.tools import FileToolsMixin, RAGToolsMixin

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class InventoryAgentConfig(LemonadeAgentConfig):
    db_path: Optional[str] = None  # path to inventory SQLite DB
    docs_path: Optional[str] = None  # path to lemonade-inventory repo


class InventoryAgent(RAGToolsMixin, FileToolsMixin, LemonadeAgent):
    """Stock levels, product lookup, and low-stock alerts."""

    AGENT_ID = "lemonade-inventory-agent"
    AGENT_NAME = "Inventory Agent"
    AGENT_DESCRIPTION = "Stock levels, product catalog, and low-stock alerts."
    CONVERSATION_STARTERS = [
        "What products are low on stock?",
        "Look up product SKU 12345",
        "How many units of X do we have?",
        "Show all products in the beverages category",
    ]

    def __init__(self, config: Optional[InventoryAgentConfig] = None):
        if config is None:
            config = InventoryAgentConfig()
        self._db_path = config.db_path
        self._docs_path = config.docs_path
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        return (
            "You are the Inventory Agent for Lemonade Store.\n\n"
            "You handle: stock level queries, product catalog lookups, low-stock alerts, "
            "and category browsing.\n\n"
            "Rules:\n"
            "- Never fabricate stock counts. Always read from the inventory database.\n"
            "- If the database path is not configured, say so explicitly.\n"
            "- All data is local — no external inventory APIs."
        )

    def _register_tools(self) -> None:
        _TOOL_REGISTRY.clear()
        if self._docs_path:
            self.register_rag_tools(self._docs_path)
        self.register_file_tools()
        self._snapshot_tools()


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Inventory Agent")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--db", default=os.getenv("INVENTORY_DB_PATH"))
    parser.add_argument("--docs", default=os.getenv("INVENTORY_DOCS_PATH"))
    args = parser.parse_args()

    config = InventoryAgentConfig(db_path=args.db, docs_path=args.docs)
    agent = InventoryAgent(config)

    if args.query:
        print(agent.process_query(args.query))
    else:
        print("Inventory Agent ready. Type your question:")
        while True:
            try:
                query = input("> ").strip()
                if query.lower() in ("exit", "quit"):
                    break
                if query:
                    print(agent.process_query(query))
            except (KeyboardInterrupt, EOFError):
                break


if __name__ == "__main__":
    main()
