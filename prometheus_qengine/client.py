import requests
import uuid
import time
import logging
from typing import Union

from .models import EuropeanOption, AsianOption, BarrierOption, SimulationResult
from .exceptions import AuthenticationError, InsufficientCreditsError, EngineComputationError, PrometheusError

logging.basicConfig(format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PrometheusClient:
    def __init__(self, api_key: str, base_url: str = "https://api.prometheusquantengine.com/api/v1"):
        if not api_key:
            raise AuthenticationError("API Key is required to instantiate the Prometheus Client.")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": self.api_key})

    def price(
        self, 
        option: Union[EuropeanOption, AsianOption, BarrierOption], 
        idempotency_key: str = None,
        poll_interval: int = 2
    ) -> SimulationResult:
        """
        Submits the mathematical payload to the C++ Engine. 
        Automatically handles synchronous routing and asynchronous HPC polling.
        """
        # Auto-generate idempotency protection if not explicitly provided
        idem_key = idempotency_key or str(uuid.uuid4())
        
        headers = {
            "Idempotency-Key": idem_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/simulations"
        payload = option.model_dump(mode='json', exclude_none=True)
        
        response = self._session.post(url, json=payload, headers=headers)
        
        self._handle_http_errors(response)
        data = response.json()
        
        # 1. Asynchronous HPC Offload Detected
        if "task_id" in data:
            task_id = data["task_id"]
            logger.info(f"Massive workload detected. Delegated to Celery HPC. Task ID: {task_id}")
            return self._poll_hpc_cluster(task_id, poll_interval)
            
        # 2. Synchronous Execution
        return SimulationResult(**data)

    def _poll_hpc_cluster(self, task_id: str, poll_interval: int) -> SimulationResult:
        """Internal method to abstract the long-polling architecture from the developer."""
        url = f"{self.base_url}/simulations/task/{task_id}"
        
        while True:
            response = self._session.get(url)
            self._handle_http_errors(response)
            data = response.json()
            status = data.get("status")
            
            if status == "SUCCESS":
                return SimulationResult(**data)
            elif status in ["FAILURE", "REVOKED"]:
                raise EngineComputationError("C++ Engine collapsed during execution. Credits refunded.")
                
            time.sleep(poll_interval)

    def _handle_http_errors(self, response: requests.Response):
        """Translates REST errors into Pythonic Exceptions."""
        if response.status_code >= 400:
            if response.status_code == 401:
                raise AuthenticationError("Invalid API Key.")
            elif response.status_code == 402:
                raise InsufficientCreditsError("Insufficient Compute Credits. Please recharge your ledger.")
            else:
                error_msg = response.json().get("detail", response.text)
                raise PrometheusError(f"HTTP {response.status_code}: {error_msg}")