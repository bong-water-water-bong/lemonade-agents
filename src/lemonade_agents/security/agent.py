# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Security Agent — audit logs, agent identity, policy checks, AIBOM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.tools import _TOOL_REGISTRY
from gaia.agents.chat.tools import FileToolsMixin, RAGToolsMixin

from lemonade_agents._base import LemonadeAgent, LemonadeAgentConfig


@dataclass
class SecurityAgentConfig(LemonadeAgentConfig):
    audit_path: Optional[str] = None   # path to audit logs
    aibom_path: Optional[str] = None   # path to AIBOM manifests
    docs_path: Optional[str] = None


class SecurityAgent(RAGToolsMixin, FileToolsMixin, LemonadeAgent):
    """Audit logs, agent identity verification, and policy checks."""

    AGENT_ID = "lemonade-security-agent"
    AGENT_NAME = "Security Agent"
    AGENT_DESCRIPTION = "Audit logs, agent identity, policy checks, and AIBOM manifests."
    CONVERSATION_STARTERS = [
        "Show recent audit log entries",
        "Check agent identity for last transaction",
        "Are there any policy violations?",
        "Show the current AIBOM manifest",
    ]

    def __init__(self, config: Optional[SecurityAgentConfig] = None):
        if config is None:
            config = SecurityAgentConfig()
        self._audit_path = config.audit_path
        self._aibom_path = config.aibom_path
        self._docs_path = config.docs_path
        super().__init__(config)

    def _get_system_prompt(self) -> str:
        return (
            "You are the Security Agent for Lemonade Store.\n\n"
            "You handle: audit log review, agent identity verification, "
            "policy compliance checks, and AIBOM (AI Bill of Materials) manifests.\n\n"
            "Rules:\n"
            "- Treat audit data as read-only — never modify logs.\n"
            "- Flag policy violations clearly and suggest remediation.\n"
            "- All security data is local — no external threat intel feeds.\n"
            "- When in doubt about a finding, escalate to the store owner."
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

    parser = argparse.ArgumentParser(description="Security Agent")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--audit", default=os.getenv("SECURITY_AUDIT_PATH"))
    parser.add_argument("--aibom", default=os.getenv("SECURITY_AIBOM_PATH"))
    parser.add_argument("--docs", default=os.getenv("SECURITY_DOCS_PATH"))
    args = parser.parse_args()

    config = SecurityAgentConfig(
        audit_path=args.audit, aibom_path=args.aibom, docs_path=args.docs
    )
    agent = SecurityAgent(config)

    if args.query:
        print(agent.process_query(args.query))
    else:
        print("Security Agent ready. Type your question:")
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
