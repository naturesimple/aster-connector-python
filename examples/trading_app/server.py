"""FastAPI trading service for running on a Google Cloud VM.

这个模块提供一个可以部署到 Google Cloud 虚拟机上的 FastAPI 交易服务，
用于暴露账户余额、持仓信息以及下单接口，供本地客户端通过网络调用。"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aster.error import ClientError
from aster.rest_api import Client

load_dotenv()


def _env(name: str) -> str:
    """Fetch required environment variables.

    获取启动交易服务所需的环境变量，并在缺失时抛出异常，确保服务运行时
    一定拥有访问 Aster API 所需的密钥。"""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required to start the trading service.")
    return value


@lru_cache()
def get_client() -> Client:
    """Return a cached API client configured with environment credentials.

    返回一个使用环境变量中凭证初始化的 Aster API 客户端，并通过 LRU 缓存
    避免重复创建实例，从而提升请求处理效率。"""
    return Client(key=_env("ASTER_API_KEY"), secret=_env("ASTER_API_SECRET"))


class AccountOverview(BaseModel):
    balances: List[Dict[str, Any]]
    positions: List[Dict[str, Any]]
    has_open_positions: bool


class OrderRequest(BaseModel):
    symbol: str
    side: str
    type: str = "MARKET"
    quantity: float
    price: Optional[float] = None
    timeInForce: Optional[str] = None
    reduceOnly: Optional[bool] = None
    newClientOrderId: Optional[str] = None
    recvWindow: Optional[int] = None

    class Config:
        extra = "allow"

    def to_api_params(self) -> Dict[str, Any]:
        """Convert the request to API parameters.

        将请求模型转换成去除空值后的字典，直接用于调用 Aster 下单接口。"""
        return self.dict(exclude_none=True)


class EnsurePositionRequest(OrderRequest):
    """Ensure that a position exists for the requested symbol.

    请求体在标准下单参数的基础上，明确表示调用者希望目标交易对存在持仓；
    如若没有持仓，将自动下单建立新仓位。"""


class EnsurePositionResponse(BaseModel):
    has_position: bool
    position: Optional[Dict[str, Any]] = None
    order_placed: bool = False
    order_response: Optional[Dict[str, Any]] = None


app = FastAPI(title="Aster Trading Gateway", version="1.0.0")


def _has_open_position(positions: List[Dict[str, Any]], symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Determine whether there is an open position for the optional symbol.

    遍历账户持仓列表，支持按照指定交易对筛选；若存在数量不为零的持仓，
    则返回对应的持仓信息，否则返回 ``None``。"""
    for position in positions:
        if symbol and position.get("symbol") != symbol:
            continue
        try:
            quantity = float(position.get("positionAmt", 0))
        except (TypeError, ValueError):
            quantity = 0
        if abs(quantity) > 0:
            return position
    return None


def _handle_client_error(error: ClientError) -> HTTPException:
    """Convert an SDK ClientError into an HTTPException.

    将 Aster SDK 抛出的 ``ClientError`` 转换成 FastAPI 友好的 ``HTTPException``，
    并保留服务端返回的错误明细，方便客户端定位问题。"""
    detail = {
        "code": error.error_code,
        "message": error.error_message,
        "status_code": error.status_code,
        "header": error.header,
    }
    return HTTPException(status_code=error.status_code or 400, detail=detail)


@app.get("/account", response_model=AccountOverview)
def account_overview() -> AccountOverview:
    """Return account balances and open positions.

    查询账户当前余额及持仓列表，同时判断是否存在任意非零持仓，结果将
    作为统一结构返回给客户端。"""
    client = get_client()
    try:
        balances = client.balance()
        positions = client.get_position_risk()
    except ClientError as error:
        raise _handle_client_error(error) from error

    open_position = _has_open_position(positions)
    return AccountOverview(
        balances=balances,
        positions=positions,
        has_open_positions=open_position is not None,
    )


@app.post("/orders")
def create_order(order: OrderRequest) -> Dict[str, Any]:
    """Forward an order creation request to the exchange.

    将客户端提交的下单参数转发到 Aster 交易所，并返回原始响应结果。"""
    client = get_client()
    payload = order.to_api_params()
    try:
        response = client.new_order(**payload)
    except ClientError as error:
        raise _handle_client_error(error) from error
    return {"order": response}


@app.post("/ensure-position", response_model=EnsurePositionResponse)
def ensure_position(request: EnsurePositionRequest) -> EnsurePositionResponse:
    """Ensure a position exists for the symbol, placing an order if required.

    首先检查目标交易对是否已有持仓；若没有，则使用请求参数补建仓位，
    并将执行结果反馈给调用方。"""
    client = get_client()
    try:
        positions = client.get_position_risk()
    except ClientError as error:
        raise _handle_client_error(error) from error

    position = _has_open_position(positions, symbol=request.symbol)
    if position:
        return EnsurePositionResponse(has_position=True, position=position)

    payload = request.to_api_params()
    try:
        order_response = client.new_order(**payload)
    except ClientError as error:
        raise _handle_client_error(error) from error

    return EnsurePositionResponse(
        has_position=False,
        order_placed=True,
        order_response=order_response,
    )


@app.get("/ping")
def ping() -> Dict[str, str]:
    """Simple health check endpoint.

    提供一个最简单的连通性检测接口，便于部署后确认服务是否存活。"""
    return {"status": "ok"}

