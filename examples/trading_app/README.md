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

