# aster-connector-python 中文指南

本项目提供了一个轻量级的 Python 库，用于连接 [Aster Finance 公共 API](https://github.com/asterdex/api-docs)。
同时，我们也在 `examples` 目录下提供了示例程序，帮助你快速搭建交易服务并通过命令行客户端进行交互。

## 安装

```bash
pip install aster-connector-python
```

## 快速开始

```python
from aster.rest_api import Client

# 获取服务器时间
client = Client()
print(client.time())

client = Client(key="<api_key>", secret="<api_secret>")

# 查询账户信息
print(client.account())

# 创建新订单
params = {
    "symbol": "BTCUSDT",
    "side": "SELL",
    "type": "LIMIT",
    "timeInForce": "GTC",
    "quantity": 0.002,
    "price": 59808,
}

response = client.new_order(**params)
print(response)
```

更多可用接口请查阅 `examples` 目录以及项目源码注释。

## 示例：云端交易服务

`examples/trading_app` 目录提供了一个可以部署在 Google Cloud 虚拟机上的 FastAPI 服务，
用于代理 Aster 交易所接口并对外暴露账户查询、自动建仓以及自定义下单等能力。

* `server.py`：运行在云服务器上的 FastAPI 应用，负责转发请求到 Aster API。
* `client.py`：运行在本地电脑的命令行客户端，可读取账户信息并发起下单请求。
* `requirements.txt`：示例所需的额外依赖列表。

### 启动服务

在云端虚拟机上配置环境变量并启动服务：

```bash
export ASTER_API_KEY="<your_api_key>"
export ASTER_API_SECRET="<your_api_secret>"
uvicorn examples.trading_app.server:app --host 0.0.0.0 --port 8000
```

### 本地访问

```bash
python examples/trading_app/client.py --server http://<vm_ip>:8000 account
```

客户端还支持 `order` 与 `ensure-position` 子命令，帮助你快速下单或自动建立持仓。

## 其他资源

* `README.md`：英文版本的项目介绍。
* `examples/trading_app/README.md`：包含更详细的部署与安全说明。

如需更多信息，请参阅源码中的中文文档字符串以及 Aster 官方 API 文档。
