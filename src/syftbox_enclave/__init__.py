def hello() -> str:
    return "Hello from syftbox-enclave!"


from .orchestra import setup_enclave_server
from .client import connect
