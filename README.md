# Prometheus Quant Engine: Python SDK

[![PyPI version](https://badge.fury.io/py/prometheus-qengine.svg)](https://badge.fury.io/py/prometheus-qengine)
[![Python Versions](https://img.shields.io/pypi/pyversions/prometheus-qengine.svg)](https://pypi.org/project/prometheus-qengine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Prometheus Quant Engine** is an institutional-grade, High-Performance Computing (HPC) API for pricing path-dependent and exotic derivatives. 

This SDK abstracts the complexity of our underlying C++ OpenMP infrastructure, allowing quantitative developers to offload massive stochastic matrices (up to 1,000,000,000 trajectories) directly from Python, completely bypassing the Global Interpreter Lock (GIL) and native memory bottlenecks.

## 🚀 Key Architectural Features

* **Strict Mathematical Validation:** Built on top of `Pydantic V2`. The SDK catches logical errors (e.g., negative time, invalid barrier boundaries) locally before wasting network latency or compute credits.
* **Deterministic Idempotency:** Built-in Double-Spend protection. If a network partition occurs, retrying the exact same request with the same `Idempotency-Key` yields the cached mathematical matrix at strictly zero cost.
* **Asynchronous Polling Abstraction:** Massive workloads ($N \times M > 50\text{M}$ steps) are seamlessly routed to our Celery HPC cluster. The SDK abstracts the long-polling lifecycle—you just call `.price()` and receive the finalized DataFrame.
* **Pandas Native:** Seamless integration with `pandas` for immediate volatility surface plotting and quantitative analysis.

## 📦 Installation

```bash
pip install prometheus-qengine
```

## 🔑 Authentication & Free Compute Ledger

To execute simulations, you need a Master API Key.
Register at [prometheusquantengine.com](https://prometheusquantengine.com) to instantly receive **50 Free Compute Credits** (equivalent to 12.5 Billion stochastic path evolutions).

## 💻 Quickstart: European Options

European options are evaluated via highly optimized Control Variates to tighten the Confidence Interval (CI) in record time.

```python
from prometheus_qengine import PrometheusClient, EuropeanOption, OptionType

# 1. Initialize the client
client = PrometheusClient(api_key="pmt_live_your_secure_api_key")

# 2. Define the exact quantitative parameters
option = EuropeanOption(
    s_0=100.0,
    strike=100.0,
    volatility=0.20,
    time_to_maturity=1.0,
    risk_free_rate=0.05,
    option_type=OptionType.CALL,
    n_simulations=10_000_000,
    label="Quickstart_European_Call"
)

# 3. Dispatch to the C++ Engine
result = client.price(option)

# 4. Analyze the output natively in Pandas
df = result.to_pandas()
print(df[["fair_value", "delta", "gamma", "vega", "credits_cost"]])
```

## ⚡ Heavy Workloads: Barrier Options (HPC Routing)

When pricing complex path-dependent instruments with step-function discontinuities (like Knock-Out barriers), dense trajectory matrices are required to stabilize the Gamma ($\Gamma$).

If your configuration exceeds 50 million total computational steps, the SDK automatically routes the payload to the asynchronous Celery broker and handles the polling loop silently.

```python
from prometheus_qengine import PrometheusClient, BarrierOption, OptionType, BarrierType

client = PrometheusClient(api_key="pmt_live_your_secure_api_key")

heavy_barrier = BarrierOption(
    s_0=100.0,
    strike=100.0,
    volatility=0.25,
    time_to_maturity=1.0,
    risk_free_rate=0.05,
    option_type=OptionType.PUT,
    n_simulations=1_000_000,       # 1 Million Paths
    m_steps=252,                   # Daily observations
    barrier_type=BarrierType.DOWN_AND_OUT,
    barrier_level=85.0
)

# The SDK detects 252,000,000 total steps.
# It delegates the matrix to the C++ cluster and waits for the resolution.
result = client.price(heavy_barrier)

print(f"Fair Value computed: {result.fair_value}")
print(f"Confidence Interval: [{result.ci_lower}, {result.ci_upper}]")
```

## 🛡️ Error Handling & Limits

The SDK translates HTTP status codes into strict Pythonic exceptions:

```python
from prometheus_qengine.exceptions import InsufficientCreditsError, AuthenticationError

try:
    result = client.price(option)
except InsufficientCreditsError as e:
    print("Ledger depleted. Recharge required.")
except AuthenticationError as e:
    print("Invalid API Key.")
```

## 📚 Documentation & Research

For in-depth mathematical proofs regarding our Finite Difference implementations, False Sharing mitigation in OpenMP, and structural REST API architecture, visit our [Papers](https://prometheusquantengine.com/papers) and [Api-docs](https://prometheusquantengine.com/web-docs).

## 📄 License

This SDK is distributed under the MIT License. See [`LICENSE`](https://github.com/Prometheus-Quant-Engineering/prometheus-quant-python/blob/main/LICENSE) for more information.