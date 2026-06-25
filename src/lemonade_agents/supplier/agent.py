# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Supplier Agent — purchase orders, supplier contacts, restocking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY
from gaia.agents.chat.tools import FileToolsMixin, RAGToolsMixin

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class SupplierAgentConfig(LemonadeAgentConfig):
    orders_path: Optional[str] = None  # path to purchase orders data
    docs_path: Optional[str] = None


class SupplierAgent(RAGToolsMixin, FileToolsMixin, LemonadeAgent):
    """Purchase orders, supplier contacts, and restocking workflows."""

    AGENT_ID = "lemonade-supplier-agent"
    AGENT_NAME = "Supplier Agent"
    AGENT_DESCRIPTION = "Purchase orders, supplier contacts, and restocking."
    CONVERSATION_STARTERS = [
        "Show open purchase orders",
        "Which items need reordering?",
        "Contact details for supplier X",
        "Draft a restock order for beverages",
    ]

    def __init__(self, config: Optional[SupplierAgentConfig] = None):
        if config is None:
            config = SupplierAgentConfig()
        self._orders_path = config.orders_path
        self._docs_path = config.docs_path
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        return (
            "You are the Supplier Agent for Lemonade Store.\n\n"
            "You handle: purchase orders, supplier contact lookups, restock workflows, "
            "and identifying items that need reordering based on inventory levels.\n\n"
            "Rules:\n"
            "- All supplier data is local — no external procurement APIs.\n"
            "- Never place orders automatically — surface drafts for owner confirmation.\n"
            "- Cross-reference inventory levels when suggesting reorders."
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

    parser = argparse.ArgumentParser(description="Supplier Agent")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--orders", default=os.getenv("SUPPLIER_ORDERS_PATH"))
    parser.add_argument("--docs", default=os.getenv("SUPPLIER_DOCS_PATH"))
    args = parser.parse_args()

    config = SupplierAgentConfig(orders_path=args.orders, docs_path=args.docs)
    agent = SupplierAgent(config)

    if args.query:
        print(agent.process_query(args.query))
    else:
        print("Supplier Agent ready. Type your question:")
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
