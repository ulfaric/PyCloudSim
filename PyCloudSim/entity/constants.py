from enum import Enum
from pickle import PUT


class Constants(str, Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    POWER_ON = "POWER_ON"
    POWER_OFF = "POWER_OFF"
    ALLOCATED = "Allocated"
    SCHEDULED = "Scheduled"
    INITIATED = "Initiated"
    X86 = "x86"
    ARM = "ARM"
    READY = "Ready"
    DECODED = "Decoded"
    INTRANSMISSION = "InTransmission"
    POST = "POST"
    GET = "GET"
    LIST = "LIST"
    DEL = "DEL"
    PUT = "PUT"
