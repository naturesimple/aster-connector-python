"""FastAPI trading service for running on a Google Cloud VM."""
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
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required to start the trading service.")
    return value


@lru_cache()
def get_client() -> Client:
    """Return a cached API client configured with environment credentials."""
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
        return self.dict(exclude_none=True)


class EnsurePositionRequest(OrderRequest):
    """Ensure that a position exists for the requested symbol."""


class EnsurePositionResponse(BaseModel):
    has_position: bool
    position: Optional[Dict[str, Any]] = None
    order_placed: bool = False
    order_response: Optional[Dict[str, Any]] = None


app = FastAPI(title="Aster Trading Gateway", version="1.0.0")


def _has_open_position(positions: List[Dict[str, Any]], symbol: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
    detail = {
        "code": error.error_code,
        "message": error.error_message,
        "status_code": error.status_code,
        "header": error.header,
    }
    return HTTPException(status_code=error.status_code or 400, detail=detail)


@app.get("/account", response_model=AccountOverview)
def account_overview() -> AccountOverview:
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
    client = get_client()
    payload = order.to_api_params()
    try:
        response = client.new_order(**payload)
    except ClientError as error:
        raise _handle_client_error(error) from error
    return {"order": response}


@app.post("/ensure-position", response_model=EnsurePositionResponse)
def ensure_position(request: EnsurePositionRequest) -> EnsurePositionResponse:
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
    return {"status": "ok"}

