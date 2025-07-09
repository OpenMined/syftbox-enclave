from enum import Enum

class DatasetStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"