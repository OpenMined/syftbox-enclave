from time import sleep
from syft_core import Client
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from loguru import logger

APP_NAME = "enclave"
KEYS_DIR = "keys"
PUBLIC_KEY_FILE = "public_key.pem"
PRIVATE_KEY_FILE = "private_key.pem"


# Exception name to indicate the state cannot advance
# as there are some pre-requisites that are not met
class StateNotReady(Exception):
    pass

def get_app_private_data(client: Client, app_name: str) -> Path:
    """
    Returns the private data directory of the app
    """
    return client.workspace.data_dir / "private" / app_name



def init_enclave(client: Client):
    """
    Initializes the enclave directories with the given client.
    """
    # Initialize the enclave with the client
    app_data_dir = client.app_data(APP_NAME)
    app_data_dir.mkdir(parents=True, exist_ok=True)

    # Create the private data directory for the app
    # This is where the private keys will be stored
    app_pvt_dir = get_app_private_data(client, APP_NAME)
    app_pvt_dir.mkdir(parents=True, exist_ok=True)


    # Enclave Job Directory is used by the enclave to store job data
    # that it intends to execute
    job_dir = app_data_dir / "jobs"

    for folder in ["launch", "running", "done"]:
        job_folder = job_dir / folder
        job_folder.mkdir(parents=True, exist_ok=True)


def create_key_pair(client: Client):
    """
    Creates a new Public/Private key pair and saves it to a file.
    """

    public_key_path = client.app_data(APP_NAME) / KEYS_DIR / PUBLIC_KEY_FILE
    private_key_path = client.app_data(APP_NAME) / KEYS_DIR / PRIVATE_KEY_FILE
    
    # Step 1:  if keys already exist, return
    if public_key_path.exists() and private_key_path.exists():
        logger.info("Key pair already exists.")
        return
    
    # Step 2: Create new key pair
    public_key_path.parent.mkdir(parents=True, exist_ok=True)
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,  # or 4096 for higher security
    )

    # Derive public key from private key
    public_key = private_key.public_key()

    # Step 3.1: Save the private key to a file
    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    logger.info(f"Private key saved to {private_key_path}")

    # Step 3.2: Save the public key to a file
    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    logger.info(f"Public key saved to {public_key_path}")

def launch_enclave_project(client: Client):
    pass

def advance_enclave_project(client: Client):
    """
    Advances the enclave project to the next state.
    """
    pass


if __name__ == "__main__":

    client = Client.load()

    init_enclave(client)
    
    create_key_pair()

    while True:
        
        try:

            launch_enclave_project(client)

            advance_enclave_project(client)

        except StateNotReady as e:
            logger.warning(f"State not ready: {e}")

        sleep(4)
    

