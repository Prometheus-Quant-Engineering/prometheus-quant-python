from enum import Enum

class OptionType(str, Enum):
    CALL = "Call"
    PUT = "Put"

class BarrierType(str, Enum):
    DOWN_AND_OUT = "DownAndOut"
    DOWN_AND_IN = "DownAndIn"
    UP_AND_OUT = "UpAndOut"
    UP_AND_IN = "UpAndIn"

class SimulationType(str, Enum):
    EUROPEAN = "European"
    ASIAN = "Asian"
    BARRIER = "Barrier"