from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal
from .enums import OptionType, BarrierType, SimulationType
import pandas as pd

class BaseSimulationPayload(BaseModel):
    s_0: float = Field(..., gt=0.0, description="Initial Asset Price (Spot)")
    strike: float = Field(..., gt=0.0, description="Strike Price")
    volatility: float = Field(..., gt=0.0, le=5.0, description="Annualized Volatility")
    time_to_maturity: float = Field(..., gt=0.0, description="Time to maturity in years")
    risk_free_rate: float = Field(..., description="Annualized Risk-Free Rate")
    option_type: OptionType
    n_simulations: int = Field(..., ge=10000, le=1000000000)
    label: Optional[str] = None
    
    simulation_type: SimulationType 

class EuropeanOption(BaseSimulationPayload):
    simulation_type: Literal[SimulationType.EUROPEAN] = SimulationType.EUROPEAN

class AsianOption(BaseSimulationPayload):
    simulation_type: Literal[SimulationType.ASIAN] = SimulationType.ASIAN
    m_steps: int = Field(..., gt=0, description="Number of temporal observation steps")

class BarrierOption(BaseSimulationPayload):
    simulation_type: Literal[SimulationType.BARRIER] = SimulationType.BARRIER
    m_steps: int = Field(..., gt=0)
    barrier_type: BarrierType
    barrier_level: float = Field(..., gt=0.0)

    @model_validator(mode='after')
    def validate_barrier_logic(self):
        """Mathematically validates that the barrier makes logical sense before computing."""
        if self.barrier_type in [BarrierType.DOWN_AND_OUT, BarrierType.DOWN_AND_IN]:
            if self.barrier_level >= self.s_0:
                raise ValueError("For Down barriers, barrier_level must be strictly below s_0.")
        elif self.barrier_type in [BarrierType.UP_AND_OUT, BarrierType.UP_AND_IN]:
            if self.barrier_level <= self.s_0:
                raise ValueError("For Up barriers, barrier_level must be strictly above s_0.")
        return self

class SimulationResult(BaseModel):
    id: str
    user_id: str
    simulation_type: str
    credits_cost: float
    created_at: str
    label: Optional[str] = None
    fair_value: float
    ci_lower: float
    ci_upper: float
    delta: Optional[float] = None
    gamma: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    is_gamma_stable: Optional[bool] = None

    def to_pandas(self) -> pd.DataFrame:
        """Transforms the payload into a clean Pandas DataFrame for quant analysis."""
        df = pd.DataFrame([self.model_dump()])
        # Optional: Set 'id' as index for cleaner display
        df.set_index('id', inplace=True)
        return df