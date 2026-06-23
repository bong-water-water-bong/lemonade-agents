"""Lemonade Store GAIA agents — offline-first, AMD NPU.

Install: pip install -e ".[web]"
Run web UI: lemonade-serve
Run an agent: lemonade-cashier "show today's sales"

Note: the web module is lazily imported — you don't need FastAPI
unless you're running the web UI.
"""

__version__ = "0.1.0"


def __getattr__(name: str):
    if name == "web_app":
        from lemonade_agents.web.app import app
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
