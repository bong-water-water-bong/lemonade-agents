# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Cashier Agent — sales transactions, payments, shift management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY, tool
from gaia.agents.chat.tools import FileToolsMixin, RAGToolsMixin

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class CashierAgentConfig(LemonadeAgentConfig):
    events_path: Optional[str] = None   # path to cashier JSONL event log
    docs_path: Optional[str] = None     # path to lemonade-cashier repo


class CashierAgent(RAGToolsMixin, FileToolsMixin, LemonadeAgent):
    """Handles sales, payments, shifts, and cash drawer queries."""

    AGENT_ID = "lemonade-cashier-agent"
    AGENT_NAME = "Cashier Agent"
    AGENT_DESCRIPTION = "Sales transactions, payments, receipts, and shift management."
    CONVERSATION_STARTERS = [
        "Show me today's sales summary",
        "How do I open a shift?",
        "What payment methods are accepted?",
        "Show last 10 transactions",
    ]

    def __init__(self, config: Optional[CashierAgentConfig] = None):
        if config is None:
            config = CashierAgentConfig()
        self._events_path = config.events_path
        self._docs_path = config.docs_path
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        return (
            "You are the Cashier Agent for Lemonade Store, an offline-first POS system "
            "running on AMD Ryzen AI hardware.\n\n"
            "You handle: sales transactions, payment processing (cash-only by default), "
            "receipts, shift open/close, cash drawer reconciliation.\n\n"
            "Rules:\n"
            "- The store is cash-only unless tap-to-pay is explicitly configured.\n"
            "- Never fabricate transaction data. Read from the event log.\n"
            "- All data stays local — no cloud, no external APIs."
        )

    def _register_tools(self) -> None:
        _TOOL_REGISTRY.clear()
        if self._docs_path:
            self.register_rag_tools(self._docs_path)
        self.register_file_tools()
        self._snapshot_tools()

        @tool
        def read_recent_transactions(limit: int = 10) -> list:
            """Read the most recent N transactions from the cashier event log."""
            if not self._events_path:
                return [{"error": "events_path not configured — set CASHIER_EVENTS_PATH"}]
            path = Path(self._events_path)
            if not path.exists():
                return [{"error": f"Event log not found: {path}"}]
            lines = path.read_text().strip().splitlines()
            events = []
            for line in reversed(lines[-limit:]):
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            return events


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Cashier Agent")
    parser.add_argument("query", nargs="?", help="Question to ask")
    parser.add_argument("--events", default=os.getenv("CASHIER_EVENTS_PATH"))
    parser.add_argument("--docs", default=os.getenv("CASHIER_DOCS_PATH"))
    args = parser.parse_args()

    config = CashierAgentConfig(events_path=args.events, docs_path=args.docs)
    agent = CashierAgent(config)

    if args.query:
        print(agent.process_query(args.query))
    else:
        print("Cashier Agent ready. Type your question:")
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
