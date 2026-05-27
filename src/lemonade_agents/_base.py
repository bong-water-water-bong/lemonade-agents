# Copyright(C) 2025-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
"""Shared offline-first base for all Lemonade Store GAIA agents."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from gaia.agents.base.agent import Agent
from gaia.agents.base.console import AgentConsole
from gaia.llm.lemonade_client import DEFAULT_LEMONADE_URL, DEFAULT_MODEL_NAME


@dataclass
class LemonadeAgentConfig:
    """Offline-first config — defaults to local Lemonade NPU server, no cloud."""

    base_url: str = ""
    model_id: Optional[str] = None
    max_steps: int = 15
    streaming: bool = True
    debug: bool = False
    show_stats: bool = False
    silent_mode: bool = False
    docs_path: Optional[str] = None  # path to index with RAG

    def __post_init__(self):
        if not self.base_url:
            self.base_url = os.getenv("LEMONADE_BASE_URL", DEFAULT_LEMONADE_URL)
        if self.model_id is None:
            self.model_id = os.getenv("LEMONADE_MODEL", DEFAULT_MODEL_NAME)


class LemonadeAgent(Agent):
    """Base for all Lemonade Store agents — always offline, always local NPU."""

    def __init__(self, config: Optional[LemonadeAgentConfig] = None):
        if config is None:
            config = LemonadeAgentConfig()
        self.config = config
        super().__init__(
            use_claude=False,
            use_chatgpt=False,
            base_url=config.base_url,
            model_id=config.model_id,
            max_steps=config.max_steps,
            streaming=config.streaming,
            debug=config.debug,
            show_stats=config.show_stats,
            silent_mode=config.silent_mode,
        )

    def _create_console(self) -> AgentConsole:
        return AgentConsole()

    def _register_tools(self) -> None:
        pass
