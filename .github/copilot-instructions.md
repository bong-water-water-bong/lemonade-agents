# Copilot Instructions — Lemonade Agents

Offline-first GAIA agents for Lemonade Store. AMD Strix Halo NPU.

## Rules
- Cash-only. No Stripe/cards/wallets. Local-first.
- GAIA agent framework. LemonadeAgent base class.
- Agents communicate via store.event.v1 events.
- No cloud calls. Everything runs on local NPU.
- Python 3.10+. Use from __future__ import annotations.

## Structure
- web/app.py — FastAPI server with POS, inventory, dashboard
- */agent.py — GAIA agents per department
- _base.py — LemonadeAgent base (local Lemonade NPU server)
