"""Lemonade Store GAIA agents — offline-first, AMD NPU.

Install: pip install -e ".[web]"
Run web UI: lemonade-serve
Run an agent: lemonade-cashier "show today's sales"
"""

from lemonade_agents.web.app import app as web_app

__all__ = ["web_app"]
__version__ = "0.1.0"
