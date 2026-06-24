# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Marketeer Agent — promotions, discounts, loyalty, customer messaging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY
from gaia.agents.chat.tools import FileToolsMixin, RAGToolsMixin

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class MarketerAgentConfig(LemonadeAgentConfig):
    campaigns_path: Optional[str] = None  # path to promotions/campaigns data
    docs_path: Optional[str] = None


class MarketerAgent(RAGToolsMixin, FileToolsMixin, LemonadeAgent):
    """Promotions, discounts, loyalty programs, and customer messaging."""

    AGENT_ID = "lemonade-marketeer-agent"
    AGENT_NAME = "Marketeer Agent"
    AGENT_DESCRIPTION = (
        "Promotions, discounts, loyalty programs, and customer messaging."
    )
    CONVERSATION_STARTERS = [
        "What promotions are active right now?",
        "Create a 10% discount for beverages",
        "Show me loyalty point balances",
        "Draft a weekend sale message",
    ]

    def __init__(self, config: Optional[MarketerAgentConfig] = None):
        if config is None:
            config = MarketerAgentConfig()
        self._campaigns_path = config.campaigns_path
        self._docs_path = config.docs_path
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        return (
            "You are the Marketeer Agent for Lemonade Store.\n\n"
            "You handle: active promotions, discount creation, loyalty programs, "
            "and drafting customer-facing messages.\n\n"
            "Rules:\n"
            "- All promotions and loyalty data are local — no cloud CRM.\n"
            "- When drafting messages, keep them concise and store-appropriate.\n"
            "- Never apply discounts directly — surface them for cashier confirmation."
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

    parser = argparse.ArgumentParser(description="Marketeer Agent")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--campaigns", default=os.getenv("MARKETEER_CAMPAIGNS_PATH"))
    parser.add_argument("--docs", default=os.getenv("MARKETEER_DOCS_PATH"))
    args = parser.parse_args()

    config = MarketerAgentConfig(campaigns_path=args.campaigns, docs_path=args.docs)
    agent = MarketerAgent(config)

    if args.query:
        print(agent.process_query(args.query))
    else:
        print("Marketeer Agent ready. Type your question:")
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
