# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Accounting Agent — daily close, cash reconciliation, CSV export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY
from gaia.agents.chat.tools import FileToolsMixin, RAGToolsMixin
from gaia.agents.tools import ScratchpadToolsMixin
from gaia.scratchpad.service import ScratchpadService

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class AccountingAgentConfig(LemonadeAgentConfig):
    reports_path: Optional[str] = None  # path to accounting reports/CSV
    docs_path: Optional[str] = None
    scratchpad_db_path: str = "~/.gaia/lemonade-accounting-scratchpad.db"


class AccountingAgent(ScratchpadToolsMixin, RAGToolsMixin, FileToolsMixin, LemonadeAgent):
    """Daily close, cash reconciliation, and financial summaries."""

    AGENT_ID = "lemonade-accounting-agent"
    AGENT_NAME = "Accounting Agent"
    AGENT_DESCRIPTION = "Daily close, cash reconciliation, and sales summaries."
    CONVERSATION_STARTERS = [
        "Run today's daily close",
        "Show me yesterday's cash reconciliation",
        "Export this week's sales to CSV",
        "What was the total revenue this month?",
    ]

    def __init__(self, config: Optional[AccountingAgentConfig] = None):
        if config is None:
            config = AccountingAgentConfig()
        self._reports_path = config.reports_path
        self._docs_path = config.docs_path
        self._scratchpad = ScratchpadService(db_path=config.scratchpad_db_path)
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        return (
            "You are the Accounting Agent for Lemonade Store.\n\n"
            "You handle: daily close procedures, cash reconciliation, sales summaries, "
            "and CSV export of financial data.\n\n"
            "Rules:\n"
            "- Use the scratchpad for all numeric calculations — never do arithmetic from memory.\n"
            "- Load raw data with insert_data, compute with query_data.\n"
            "- Never fabricate financial figures. Read from reports or event logs.\n"
            "- All data is local."
        )

    def _register_tools(self) -> None:
        _TOOL_REGISTRY.clear()
        if self._docs_path:
            self.register_rag_tools(self._docs_path)
        self.register_file_tools()
        self.register_scratchpad_tools()
        self._snapshot_tools()

    def close(self) -> None:
        if self._scratchpad:
            self._scratchpad.close_db()


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Accounting Agent")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--reports", default=os.getenv("ACCOUNTING_REPORTS_PATH"))
    parser.add_argument("--docs", default=os.getenv("ACCOUNTING_DOCS_PATH"))
    args = parser.parse_args()

    config = AccountingAgentConfig(reports_path=args.reports, docs_path=args.docs)
    agent = AccountingAgent(config)

    if args.query:
        print(agent.process_query(args.query))
    else:
        print("Accounting Agent ready. Type your question:")
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
