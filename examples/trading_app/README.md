# Trading App Example

This example demonstrates how to expose basic trading operations for the Aster exchange through a FastAPI service that can run on a Google Cloud VM. A lightweight Python client is also included so that a local machine can retrieve account information and forward order instructions to the remote service.

## Features

* Retrieve account balances and current positions from the VM.
* Determine whether there is an open position for a symbol and automatically create one if none exists.
* Submit manual orders from the local client and forward them to the VM for execution.

## Components

* `server.py` – FastAPI application meant to run on the Google Cloud VM. It proxies Aster API requests.
* `client.py` – Command line client for a local workstation. It communicates with the remote server over HTTP.
* `requirements.txt` – Additional dependencies needed for the example (FastAPI, Uvicorn, HTTPX).

## Prerequisites

1. Install the base project requirements as described in the repository README.
2. Install the example specific dependencies:

   ```bash
   pip install -r examples/trading_app/requirements.txt
   ```

3. Create an `.env` file on the VM next to `server.py` or export the following environment variables:

   * `ASTER_API_KEY`
   * `ASTER_API_SECRET`

## Running the Server on Google Cloud VM

```bash
export ASTER_API_KEY="<your_api_key>"
export ASTER_API_SECRET="<your_api_secret>"
uvicorn examples.trading_app.server:app --host 0.0.0.0 --port 8000
```

Make sure that port `8000` (or the port of your choice) is allowed through the VM firewall so that your local machine can connect to the service.

## Using the Local Client

From your local machine, configure the server URL (replace `vm-public-ip`):

```bash
python examples/trading_app/client.py --server http://vm-public-ip:8000 account
```

### Supported Client Commands

* `account` – Fetch balances and open positions.
* `ensure-position` – Ensure there is an open position for a symbol, opening one if necessary.
* `order` – Submit a custom order payload.

Run `python examples/trading_app/client.py --help` for full usage details.

## Security Notes

* The example uses plain HTTP for simplicity. Consider enabling HTTPS (via an HTTPS load balancer or a reverse proxy such as Nginx) before exposing it to the public internet.
* Secure access to the VM using firewall rules or a VPN. The Aster API credentials grant trading access and must be protected.

---

## 中文指南

该示例演示如何通过 FastAPI 在 Google Cloud 虚拟机上部署一个交易网关，
并利用随附的 Python 命令行客户端在本地读取账户信息、检查持仓以及下单。

### 功能概览

* 从云端服务器获取账户余额与当前持仓。
* 如果指定交易对没有持仓，自动创建一笔订单建立仓位。
* 通过本地客户端提交自定义订单并交由云端服务执行。

### 组件说明

* `server.py`：部署在云服务器上的 FastAPI 应用，代理 Aster API。
* `client.py`：运行在本地的命令行工具，通过 HTTP 与服务器通信。
* `requirements.txt`：示例所需的额外依赖（FastAPI、Uvicorn、HTTPX）。

### 前置条件

1. 根据仓库 `README.md` 完成基础依赖安装。
2. 安装示例依赖：

   ```bash
   pip install -r examples/trading_app/requirements.txt
   ```

3. 在虚拟机上创建 `.env` 文件或导出以下环境变量：

   * `ASTER_API_KEY`
   * `ASTER_API_SECRET`

### 启动服务器

```bash
export ASTER_API_KEY="<your_api_key>"
export ASTER_API_SECRET="<your_api_secret>"
uvicorn examples.trading_app.server:app --host 0.0.0.0 --port 8000
```

确保虚拟机防火墙开放 `8000` 端口（或你自定义的端口），以便本地客户端连接。

### 使用本地客户端

在本地机器上配置服务器地址（`vm-public-ip` 为云服务器公网 IP）：

```bash
python examples/trading_app/client.py --server http://vm-public-ip:8000 account
```

客户端支持以下子命令：

* `account`：查询余额与持仓。
* `ensure-position`：确保存在指定交易对的持仓，若没有则自动下单。
* `order`：提交自定义订单请求。

更多使用方式可执行 `python examples/trading_app/client.py --help` 查看。

### 安全提示

* 示例默认使用 HTTP，建议上线前配置 HTTPS（如通过反向代理或负载均衡器）。
* 通过防火墙或 VPN 限制访问，妥善保护具有交易权限的 Aster API 凭证。

