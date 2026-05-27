# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Lemonade Helper — user-facing gateway that routes to department agents."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY, tool
from gaia.agents.chat.tools import RAGToolsMixin

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class LemonadeHelperConfig(LemonadeAgentConfig):
    docs_path: Optional[str] = None  # path to lemonade-store repo docs


DEPARTMENTS = {
    "cashier": "Sales transactions, payments, receipts, open/close shift, cash drawer",
    "inventory": "Stock levels, product catalog, low-stock alerts, product lookup",
    "accounting": "Daily close, cash reconciliation, sales summaries, CSV export",
    "marketeer": "Promotions, discounts, loyalty, customer messaging",
    "supplier": "Purchase orders, supplier contacts, restocking",
    "reports": "Analytics, trend analysis, historical sales data",
    "security": "Audit logs, agent identity, policy checks, AIBOM",
}


class LemonadeHelperAgent(RAGToolsMixin, LemonadeAgent):
    """Gateway agent — answers store questions and routes to the right department."""

    AGENT_ID = "lemonade-helper"
    AGENT_NAME = "Lemonade Helper"
    AGENT_DESCRIPTION = "Your guide to the Lemonade Store suite. Ask anything about the store."
    CONVERSATION_STARTERS = [
        "What can you help me with?",
        "How do I do a daily close?",
        "What's the current stock on item X?",
        "Who handles supplier orders?",
    ]

    def __init__(self, config: Optional[LemonadeHelperConfig] = None):
        if config is None:
            config = LemonadeHelperConfig()
        self._docs_path = config.docs_path
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        dept_lines = "\n".join(f"  - {k}: {v}" for k, v in DEPARTMENTS.items())
        return (
            "You are Lemonade Helper, the user-facing assistant for the Lemonade Store suite.\n"
            "The store runs entirely offline on AMD Ryzen AI hardware.\n\n"
            "Departments you can route to:\n"
            f"{dept_lines}\n\n"
            "When a user asks about a specific department, tell them which agent handles it "
            "and what command to run (e.g. `lemonade-cashier`, `lemonade-inventory`). "
            "For general questions, answer directly from your knowledge of the suite. "
            "Never fabricate data like stock counts or sales figures — direct the user "
            "to the appropriate department agent for live data."
        )

    def _register_tools(self) -> None:
        _TOOL_REGISTRY.clear()
        if self._docs_path:
            self.register_rag_tools(self._docs_path)
        self._snapshot_tools()

        @tool
        def list_departments() -> dict:
            """List all Lemonade Store departments and what they handle."""
            return DEPARTMENTS

        @tool
        def route_to_department(query: str) -> str:
            """
            Given a user query, return the name of the department agent
            best equipped to answer it and the CLI command to run it.

            Use this when the user asks about something specific like stock,
            sales, accounting, suppliers, or security.
            """
            query_lower = query.lower()
            for dept, description in DEPARTMENTS.items():
                keywords = description.lower().split(", ")
                if any(k in query_lower for k in keywords):
                    return f"Route to: lemonade-{dept}\nCommand: lemonade-{dept} '{query}'"
            return (
                "No single department matched. Try lemonade-helper for general questions "
                "or describe your need more specifically."
            )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Lemonade Helper agent")
    parser.add_argument("query", nargs="?", help="Question to ask")
    parser.add_argument("--docs", help="Path to lemonade-store docs for RAG")
    args = parser.parse_args()

    config = LemonadeHelperConfig(docs_path=args.docs)
    agent = LemonadeHelperAgent(config)

    if args.query:
        response = agent.process_query(args.query)
        print(response)
    else:
        print("Lemonade Helper ready. Type your question:")
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
