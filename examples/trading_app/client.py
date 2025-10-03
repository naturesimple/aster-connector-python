"""Command line client for interacting with the trading service."""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional

import httpx


DEFAULT_SERVER = "http://localhost:8000"


def parse_extra_arguments(extra: List[str]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for argument in extra:
        if "=" not in argument:
            raise ValueError(f"Extra argument must be in key=value format: {argument}")
        key, value = argument.split("=", 1)
        parsed[key] = value
    return parsed


def request(method: str, url: str, *, json_payload: Optional[Dict[str, Any]] = None) -> Any:
    response = httpx.request(method, url, json=json_payload, timeout=30.0)
    response.raise_for_status()
    if response.content:
        return response.json()
    return None


def handle_account(args: argparse.Namespace) -> None:
    url = f"{args.server}/account"
    data = request("GET", url)
    print(json.dumps(data, indent=2, sort_keys=True))


def handle_order(args: argparse.Namespace) -> None:
    url = f"{args.server}/orders"
    payload: Dict[str, Any] = {
        "symbol": args.symbol,
        "side": args.side,
        "type": args.type,
        "quantity": args.quantity,
    }
    if args.price is not None:
        payload["price"] = args.price
    if args.time_in_force:
        payload["timeInForce"] = args.time_in_force
    if args.reduce_only is not None:
        payload["reduceOnly"] = args.reduce_only
    if args.client_order_id:
        payload["newClientOrderId"] = args.client_order_id
    if args.recv_window is not None:
        payload["recvWindow"] = args.recv_window
    payload.update(parse_extra_arguments(args.extra))

    data = request("POST", url, json_payload=payload)
    print(json.dumps(data, indent=2, sort_keys=True))


def handle_ensure_position(args: argparse.Namespace) -> None:
    url = f"{args.server}/ensure-position"
    payload: Dict[str, Any] = {
        "symbol": args.symbol,
        "side": args.side,
        "type": args.type,
        "quantity": args.quantity,
    }
    if args.price is not None:
        payload["price"] = args.price
    if args.time_in_force:
        payload["timeInForce"] = args.time_in_force
    if args.recv_window is not None:
        payload["recvWindow"] = args.recv_window
    payload.update(parse_extra_arguments(args.extra))

    data = request("POST", url, json_payload=payload)
    print(json.dumps(data, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Client for the Aster trading gateway")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Base URL of the trading server")

    subparsers = parser.add_subparsers(dest="command", required=True)

    account_parser = subparsers.add_parser("account", help="Fetch balances and open positions")
    account_parser.set_defaults(func=handle_account)

    ensure_parser = subparsers.add_parser(
        "ensure-position", help="Ensure an open position exists; place an order if not"
    )
    ensure_parser.add_argument("symbol", help="Trading symbol, e.g. BTCUSDT")
    ensure_parser.add_argument("side", help="Order side (BUY or SELL)")
    ensure_parser.add_argument("quantity", type=float, help="Order quantity")
    ensure_parser.add_argument("--type", default="MARKET", help="Order type (default: MARKET)")
    ensure_parser.add_argument("--price", type=float, help="Limit price")
    ensure_parser.add_argument("--time-in-force", dest="time_in_force", help="Time in force policy")
    ensure_parser.add_argument("--recv-window", dest="recv_window", type=int, help="Custom recvWindow")
    ensure_parser.add_argument(
        "--extra",
        nargs="*",
        default=[],
        help="Additional key=value pairs forwarded to the API",
    )
    ensure_parser.set_defaults(func=handle_ensure_position)

    order_parser = subparsers.add_parser("order", help="Submit a raw order payload")
    order_parser.add_argument("symbol", help="Trading symbol, e.g. BTCUSDT")
    order_parser.add_argument("side", help="Order side (BUY or SELL)")
    order_parser.add_argument("type", help="Order type, e.g. MARKET or LIMIT")
    order_parser.add_argument("quantity", type=float, help="Order quantity")
    order_parser.add_argument("--price", type=float, help="Limit price")
    order_parser.add_argument("--time-in-force", dest="time_in_force", help="Time in force policy")
    order_parser.add_argument("--reduce-only", dest="reduce_only", action="store_true")
    order_parser.add_argument("--no-reduce-only", dest="reduce_only", action="store_false")
    order_parser.set_defaults(reduce_only=None)
    order_parser.add_argument("--client-order-id", dest="client_order_id", help="Client order identifier")
    order_parser.add_argument("--recv-window", dest="recv_window", type=int, help="Custom recvWindow")
    order_parser.add_argument(
        "--extra",
        nargs="*",
        default=[],
        help="Additional key=value pairs forwarded to the API",
    )
    order_parser.set_defaults(func=handle_order)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as error:
        print(error)
        raise SystemExit(1) from error
    except httpx.HTTPError as error:
        print(f"Request failed: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

