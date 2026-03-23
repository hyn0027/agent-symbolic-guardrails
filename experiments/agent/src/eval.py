from enum import Enum


class TerminateReason(Enum):
    USER_STOP = "USER_STOP"
    MAX_STEPS = "MAX_STEPS"
    AGENT_STOP = "AGENT_STOP"
