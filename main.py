import shutil
from time import sleep
from syft_core import Client
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from loguru import logger
import yaml

from utils import validate_config_file

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

    for folder in ["launch", "running", "done", "outputs"]:
        job_folder = job_dir / folder
        job_folder.mkdir(parents=True, exist_ok=True)

def get_public_key_path(client: Client) -> Path:
    """
    Returns the public key path of the app
    """
    return client.app_data(APP_NAME) / KEYS_DIR / PUBLIC_KEY_FILE

def get_private_key_path(client: Client) -> Path:
    """
    Returns the private key path of the app
    """
    return get_app_private_data(client, APP_NAME) / KEYS_DIR / PRIVATE_KEY_FILE

def create_key_pair(client: Client):
    """
    Creates a new Public/Private key pair and saves it to a file.
    """

    public_key_path = get_public_key_path(client)
    private_key_path = get_private_key_path(client)
    
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

def verify_data_sources(client: Client, config_file_path: Path) -> bool:
    """
    Verifies if all the required files are present in the data sources.
    """
    # Load the config file
    with open(config_file_path, "r") as f:
        config_file = yaml.safe_load(f)

    # Get the data sources from the config file
    data_sources = config_file.get("data", [])

    # Check if all the required files are present
    for source in data_sources:
        datasite, dataset_id = source


    return True



def launch_enclave_project(client: Client):
    """
    Launches the enclave project with the given client.
    """
    launch_dir = client.app_data(APP_NAME) / "jobs" / "launch"
    running_dir = client.app_data(APP_NAME) / "jobs" / "running"
    # Iterates through each folder inside the launch folder and looks for 
    # config.yaml file and code directory
    for folder in launch_dir.iterdir():
        if folder.is_dir():
            config_file_path = folder / "config.yaml"
            code_dir = folder / "code"
            if not config_file_path.exists() and not code_dir.exists():
                logger.warning(f"Config file or code directory not found in {folder}")
                continue
            # Check if the config file is valid
            validate_config_file(config_file_path)

            # Check if all the required files are sent by the datasites
            verify_sources = verify_data_sources(client, config_file_path)

            # if all the files are present, move the folder to the running directory
            if verify_sources:
                logger.info(f"Moving {folder} to running directory")
                # Move the folder to the running directory
                shutil.move(folder, running_dir / folder.name)


if __name__ == "__main__":

    client = Client.load()

    init_enclave(client)
    
    create_key_pair(client)

    while True:
        
        # Check if the enclave is ready to launch
        launch_enclave_project(client)

        sleep(4)
    

