import requests
import uuid
import time
import logging
from typing import Optional, Union

from .models import EuropeanOption, AsianOption, BarrierOption, SimulationResult
from .exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    EngineComputationError,
    PrometheusError,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PrometheusClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.prometheusquantengine.com/api/v1",
        timeout: int = 60,
    ):
        if not api_key:
            raise AuthenticationError("API Key is required to instantiate the Prometheus Client.")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": self.api_key})

    def price(
        self,
        option: Union[EuropeanOption, AsianOption, BarrierOption],
        idempotency_key: Optional[str] = None,
        poll_interval: int = 2,
    ) -> SimulationResult:
        """
        Submits the mathematical payload to the C++ Engine.
        Automatically handles synchronous routing and asynchronous HPC polling.
        """
        idem_key = idempotency_key or str(uuid.uuid4())

        headers = {
            "Idempotency-Key": idem_key,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/simulations"
        payload = option.model_dump(mode="json", exclude_none=True)

        response = self._session.post(url, json=payload, headers=headers, timeout=self.timeout)
        self._handle_http_errors(response)
        data = response.json()

        # 1. Asynchronous HPC Offload Detected
        if "task_id" in data:
            task_id = data["task_id"]
            logger.info("Massive workload detected. Delegated to Celery HPC. Task ID: %s", task_id)
            return self._poll_hpc_cluster(task_id, poll_interval)

        # 2. Synchronous Execution
        return SimulationResult(**data)

    def _poll_hpc_cluster(self, task_id: str, poll_interval: int) -> SimulationResult:
        """Polls the task status endpoint and fetches the full SimulationResponse upon completion."""
        task_url = f"{self.base_url}/simulations/task/{task_id}"

        while True:
            response = self._session.get(task_url, timeout=self.timeout)
            self._handle_http_errors(response)
            data = response.json()
            status = data.get("status")

            if status == "SUCCESS":
                sim_id = data.get("simulation_id")
                if not sim_id:
                    raise EngineComputationError("Task succeeded but returned no simulation_id.")
                return self._fetch_simulation_result(sim_id)

            if status in ("FAILURE", "REVOKED"):
                raise EngineComputationError("C++ Engine collapsed during execution. Credits refunded.")

            time.sleep(poll_interval)

    def _fetch_simulation_result(self, simulation_id: str, retries: int = 4) -> SimulationResult:
        """Retrieves the complete persisted simulation matrix by UUID with brief retry tolerance."""
        detail_url = f"{self.base_url}/simulations/{simulation_id}"

        for attempt in range(retries):
            response = self._session.get(detail_url, timeout=self.timeout)
            if response.status_code == 404 and attempt < retries - 1:
                time.sleep(1.5)
                continue
            self._handle_http_errors(response)
            return SimulationResult(**response.json())

        raise EngineComputationError(f"Simulation {simulation_id} completed but could not be retrieved.")

    def _handle_http_errors(self, response: requests.Response) -> None:
        """Translates REST errors into Pythonic Exceptions safely."""
        if response.status_code >= 400:
            try:
                body = response.json()
                error_msg = body.get("detail", response.text) if isinstance(body, dict) else response.text
            except ValueError:
                error_msg = response.text

            if response.status_code == 401:
                raise AuthenticationError("Invalid API Key.")
            if response.status_code == 402:
                raise InsufficientCreditsError(f"Insufficient Compute Credits: {error_msg}")
            raise PrometheusError(f"HTTP {response.status_code}: {error_msg}")