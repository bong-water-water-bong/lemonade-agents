"""Lemonade Agents Web Server — internal POS + Inventory + Dashboard.

Starts a local FastAPI server with:
- /           → POS (Point of Sale) interface
- /inventory  → Product onboarding and stock management
- /dashboard  → Owner dashboard with daily summaries
- /api/...    → REST API for all departments

No cloud. No npm. No build step. Runs entirely offline on Strix Halo.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR = Path.home() / ".lemonade" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_PATH = DATA_DIR / "store_events.jsonl"
DB_PATH = DATA_DIR / "inventory.db"

app = FastAPI(title="Lemonade Store", version="0.1.0")

# ---------------------------------------------------------------------------
# In-memory cart (per session — offline, single till)
# ---------------------------------------------------------------------------
_current_cart: list[dict[str, Any]] = []
_store_id = "tie-dye-farms"


def _write_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    event = {
        "schema_version": "store.event.v1",
        "event_id": f"evt-{uuid.uuid4().hex[:12]}",
        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "store_id": _store_id,
        "department": _dept_from_type(event_type),
        "type": event_type,
        "source": "lemonade-web",
        "actor": {"kind": "attendant", "id": "web-ui"},
        "requires_approval": False,
        "approved_by": None,
        "payload": payload,
    }
    with open(EVENTS_PATH, "a") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def _dept_from_type(event_type: str) -> str:
    return event_type.split(".")[0]


def _read_events(event_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if not EVENTS_PATH.exists():
        return []
    events: list[dict[str, Any]] = []
    with open(EVENTS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
                if event_type is None or evt.get("type") == event_type:
                    events.append(evt)
            except json.JSONDecodeError:
                pass
    return events[-limit:]


# ---------------------------------------------------------------------------
# POS API
# ---------------------------------------------------------------------------

@app.post("/api/cart/add")
async def cart_add(request: Request) -> JSONResponse:
    data = await request.json()
    sku = data.get("sku", "").strip()
    name = data.get("name", "").strip()
    price = data.get("price", 0)
    quantity = data.get("quantity", 1)

    if not sku or not name:
        raise HTTPException(400, "sku and name required")

    for item in _current_cart:
        if item["sku"] == sku:
            item["quantity"] += quantity
            break
    else:
        _current_cart.append({
            "sku": sku, "name": name, "price": float(price),
            "quantity": quantity, "taxable": data.get("taxable", True),
        })

    _write_event("cashier.transaction.line_added", {
        "sku": sku, "name": name, "price": str(price), "quantity": quantity,
    })

    return JSONResponse({"cart": _current_cart, "total": _cart_total()})


@app.post("/api/cart/remove")
async def cart_remove(request: Request) -> JSONResponse:
    data = await request.json()
    sku = data.get("sku", "")
    _current_cart[:] = [i for i in _current_cart if i["sku"] != sku]
    return JSONResponse({"cart": _current_cart, "total": _cart_total()})


@app.post("/api/cart/checkout")
async def cart_checkout(request: Request) -> JSONResponse:
    global _current_cart
    data = await request.json()
    cash_tendered = float(data.get("cash_tendered", 0))
    total = _cart_total()

    if cash_tendered < total:
        raise HTTPException(400, f"Insufficient cash: ${cash_tendered:.2f} < ${total:.2f}")

    change = round(cash_tendered - total, 2)
    items = [{
        "sku": i["sku"], "name": i["name"],
        "quantity": i["quantity"], "unit_price": f"{i['price']:.2f}",
    } for i in _current_cart]

    _write_event("cashier.transaction.closed", {
        "total": f"{total:.2f}",
        "cash_tendered": f"{cash_tendered:.2f}",
        "change": f"{change:.2f}",
        "items": items,
    })

    receipt = {"items": _current_cart, "total": total, "cash_tendered": cash_tendered, "change": change}
    _current_cart = []
    return JSONResponse({"receipt": receipt, "success": True})


@app.get("/api/cart")
async def cart_get() -> JSONResponse:
    return JSONResponse({"cart": _current_cart, "total": _cart_total()})


def _cart_total() -> float:
    return round(sum(i["price"] * i["quantity"] for i in _current_cart), 2)


# ---------------------------------------------------------------------------
# Inventory API
# ---------------------------------------------------------------------------

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS products (
        sku TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'general',
        unit_price TEXT NOT NULL DEFAULT '0.00', taxable INTEGER DEFAULT 1,
        reorder_threshold INTEGER DEFAULT 0, zone TEXT DEFAULT '', shelf TEXT DEFAULT '',
        aliases TEXT DEFAULT '', stock INTEGER DEFAULT 0
    )""")
    conn.commit()
    return conn


@app.get("/api/inventory/products")
async def inventory_list(category: str = "") -> JSONResponse:
    conn = _get_db()
    if category:
        rows = conn.execute("SELECT * FROM products WHERE category=? ORDER BY name", (category,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products ORDER BY category, name").fetchall()
    return JSONResponse([dict(r) for r in rows])


@app.post("/api/inventory/products")
async def inventory_add(request: Request) -> JSONResponse:
    data = await request.json()
    sku = data.get("sku", "").strip()
    if not sku:
        raise HTTPException(400, "sku required")
    conn = _get_db()
    conn.execute(
        """INSERT OR REPLACE INTO products
           (sku, name, category, unit_price, taxable, reorder_threshold, zone, shelf, aliases, stock)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (sku, data.get("name", ""), data.get("category", "general"),
         str(data.get("unit_price", "0.00")), 1 if data.get("taxable", True) else 0,
         data.get("reorder_threshold", 0), data.get("zone", ""), data.get("shelf", ""),
         data.get("aliases", ""), data.get("stock", 0)),
    )
    conn.commit()

    _write_event("inventory.created", {
        "sku": sku, "name": data.get("name", ""),
        "category": data.get("category", "general"),
        "initial_quantity": data.get("stock", 0),
    })

    return JSONResponse({"success": True, "sku": sku})


@app.put("/api/inventory/products/{sku}")
async def inventory_update(sku: str, request: Request) -> JSONResponse:
    data = await request.json()
    conn = _get_db()
    existing = conn.execute("SELECT * FROM products WHERE sku=?", (sku,)).fetchone()
    if not existing:
        raise HTTPException(404, f"SKU {sku} not found")

    old_stock = existing["stock"]
    new_stock = data.get("stock", old_stock)

    conn.execute(
        """UPDATE products SET name=?, category=?, unit_price=?, taxable=?,
           reorder_threshold=?, zone=?, shelf=?, aliases=?, stock=?
           WHERE sku=?""",
        (data.get("name", existing["name"]), data.get("category", existing["category"]),
         str(data.get("unit_price", existing["unit_price"])),
         1 if data.get("taxable", True) else 0,
         data.get("reorder_threshold", existing["reorder_threshold"]),
         data.get("zone", existing["zone"]), data.get("shelf", existing["shelf"]),
         data.get("aliases", existing["aliases"]), new_stock, sku),
    )
    conn.commit()

    delta = new_stock - old_stock
    if delta != 0:
        _write_event("inventory.adjusted", {"sku": sku, "delta": delta, "reason": "manual update"})

    return JSONResponse({"success": True})


@app.delete("/api/inventory/products/{sku}")
async def inventory_delete(sku: str) -> JSONResponse:
    conn = _get_db()
    conn.execute("DELETE FROM products WHERE sku=?", (sku,))
    conn.commit()
    return JSONResponse({"success": True})


# ---------------------------------------------------------------------------
# Dashboard API
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/summary")
async def dashboard_summary() -> JSONResponse:
    events = _read_events(limit=200)
    sales = sum(1 for e in events if e.get("type") == "cashier.transaction.closed")
    sales_total = 0.0
    for e in events:
        if e.get("type") == "cashier.transaction.closed":
            try:
                sales_total += float(e.get("payload", {}).get("total", 0))
            except (ValueError, TypeError):
                pass

    conn = _get_db()
    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    low_stock = conn.execute(
        "SELECT COUNT(*) FROM products WHERE stock > 0 AND stock <= reorder_threshold"
    ).fetchone()[0]

    return JSONResponse({
        "store_id": _store_id,
        "transactions_today": sales,
        "sales_total": f"${sales_total:.2f}",
        "products_in_catalog": product_count,
        "low_stock_items": low_stock,
        "pending_approvals": 0,
    })


@app.get("/api/dashboard/recent")
async def dashboard_recent() -> JSONResponse:
    events = _read_events(limit=20)
    return JSONResponse(events)


# ---------------------------------------------------------------------------
# Events API
# ---------------------------------------------------------------------------

@app.get("/api/events")
async def events_list(limit: int = 50, type: str = "") -> JSONResponse:
    return JSONResponse(_read_events(event_type=type or None, limit=limit))


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def pos_page() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "pos.html").read_text())


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "inventory.html").read_text())


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "dashboard.html").read_text())


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
