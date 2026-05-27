# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Reports Agent — analytics, trends, historical sales data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY
from gaia.agents.chat.tools import FileToolsMixin, RAGToolsMixin
from gaia.agents.tools import ScratchpadToolsMixin
from gaia.scratchpad.service import ScratchpadService

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class ReportsAgentConfig(LemonadeAgentConfig):
    data_path: Optional[str] = None   # path to exported reports/CSV files
    docs_path: Optional[str] = None
    scratchpad_db_path: str = "~/.gaia/lemonade-reports-scratchpad.db"


class ReportsAgent(ScratchpadToolsMixin, RAGToolsMixin, FileToolsMixin, LemonadeAgent):
    """Analytics, trend analysis, and historical sales reporting."""

    AGENT_ID = "lemonade-reports-agent"
    AGENT_NAME = "Reports Agent"
    AGENT_DESCRIPTION = "Analytics, trend analysis, and historical sales data."
    CONVERSATION_STARTERS = [
        "Show sales trend for the last 30 days",
        "What's our best-selling product this week?",
        "Compare this month vs last month",
        "Generate a weekly summary report",
    ]

    def __init__(self, config: Optional[ReportsAgentConfig] = None):
        if config is None:
            config = ReportsAgentConfig()
        self._data_path = config.data_path
        self._docs_path = config.docs_path
        self._scratchpad = ScratchpadService(db_path=config.scratchpad_db_path)
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        return (
            "You are the Reports Agent for Lemonade Store.\n\n"
            "You handle: sales analytics, trend analysis, period comparisons, "
            "and generating summary reports from historical data.\n\n"
            "Rules:\n"
            "- Use the scratchpad for all aggregations and comparisons.\n"
            "- Load CSV/JSONL data with insert_data, compute with query_data.\n"
            "- Present numbers clearly with context (vs prior period, % change).\n"
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

    parser = argparse.ArgumentParser(description="Reports Agent")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--data", default=os.getenv("REPORTS_DATA_PATH"))
    parser.add_argument("--docs", default=os.getenv("REPORTS_DOCS_PATH"))
    args = parser.parse_args()

    config = ReportsAgentConfig(data_path=args.data, docs_path=args.docs)
    agent = ReportsAgent(config)

    if args.query:
        print(agent.process_query(args.query))
    else:
        print("Reports Agent ready. Type your question:")
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
