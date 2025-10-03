"""Command line client for interacting with the trading service.

该模块实现了一个命令行客户端，用于本地计算机与部署在云端的交易服务交互，
支持查询账户信息、检查持仓并下发新订单。"""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional

import httpx


DEFAULT_SERVER = "http://localhost:8000"


def parse_extra_arguments(extra: List[str]) -> Dict[str, Any]:
    """Parse `key=value` formatted arguments into a dictionary.

    将附加参数列表解析为字典形式，便于透传给后端 API；若格式不正确则抛出
    ``ValueError`` 并提示用户按 ``key=value`` 规范填写。"""
    parsed: Dict[str, Any] = {}
    for argument in extra:
        if "=" not in argument:
            raise ValueError(f"Extra argument must be in key=value format: {argument}")
        key, value = argument.split("=", 1)
        parsed[key] = value
    return parsed


def request(method: str, url: str, *, json_payload: Optional[Dict[str, Any]] = None) -> Any:
    """Perform an HTTP request and return JSON data when available.

    统一封装客户端的 HTTP 请求逻辑，处理超时与状态码异常，并在响应体存在
    内容时返回解析后的 JSON 数据。"""
    response = httpx.request(method, url, json=json_payload, timeout=30.0)
    response.raise_for_status()
    if response.content:
        return response.json()
    return None


def handle_account(args: argparse.Namespace) -> None:
    """Call the account endpoint and print the JSON response.

    调用远程服务的 ``/account`` 接口并格式化输出账户余额与持仓信息，方便
    用户在终端中快速查看。"""
    url = f"{args.server}/account"
    data = request("GET", url)
    print(json.dumps(data, indent=2, sort_keys=True))


def handle_order(args: argparse.Namespace) -> None:
    """Submit a raw order payload to the remote trading service.

    根据命令行参数组装下单请求，透传额外 ``key=value`` 参数，并将服务端返回
    的执行结果以 JSON 形式打印出来。"""
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
    """Ensure a position exists by calling the dedicated endpoint.

    访问 ``/ensure-position`` 接口确认指定交易对是否已有持仓，如无持仓则由
    服务端自动建仓，并展示对应返回数据。"""
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
    """Construct the CLI argument parser.

    创建并配置客户端所需的命令行参数解析器，包含查询账户、保证持仓和直接
    下单等子命令的参数说明。"""
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
    """Entrypoint for the CLI client.

    解析命令行参数后执行对应子命令，并在请求或参数错误时输出提示信息，
    以便用户快速定位问题。"""
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

