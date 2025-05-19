import os
import shutil
import subprocess
from time import sleep
from syft_core import Client
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from loguru import logger
import yaml

from utils import validate_config_file
from utils import extract_zip

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

def get_dataset_path_from_config(config_file_path: Path) -> list:
    """
    Returns the sources from the config file.
    """
    # Load the config file
    with open(config_file_path, "r") as f:
        config_file = yaml.safe_load(f)

    # Get the data sources from the config file
    data_sources = config_file.get("data", [])

    dataset_paths = []
    
    for source in data_sources:
        datasite, dataset_id = source

        enclave_data_folder = client.app_data(APP_NAME, datasite=datasite) / "data"
        dataset_path = enclave_data_folder / f"{dataset_id}.enc" 
        
        dataset_paths.append(dataset_path)

    return dataset_paths

    
    

def verify_data_sources(client: Client, config_file_path: Path) -> bool:
    """
    Verifies if all the required files are present in the data sources.
    """    
    dataset_paths: list[Path] = get_dataset_path_from_config(config_file_path)

    # Check if all the required files are present
    for dataset_path in dataset_paths:
        if not dataset_path.exists():
            logger.warning(f"Encrypted Dataset File {dataset_path} not found")
            return False

    # If all the files are present, return True
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

def decrypt_data(client: Client, enc_file_path: Path):
    """
    Decrypts the data files in the given config file.
    """
    private_key_path = get_private_key_path(client)
    # Step 1: Load the private key
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )

    # Step 2: Read the encrypted file
    with open(enc_file_path, "rb") as f:
        key_len = int.from_bytes(f.read(2), "big")
        encrypted_key = f.read(key_len)
        nonce = f.read(12)
        ciphertext = f.read()
    
    # Step 3: Decrypt the AES key using private key
    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    
    # Step 4: Decrypt the ZIP file
    aesgcm = AESGCM(aes_key)
    zip_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data=None)

    return zip_bytes

def extract_enc_data(client: Client, enc_file_path: Path, target_dir: Path):
    zip_bytes = decrypt_data(client, enc_file_path)

    # Extract the zip file to the target directory
    extract_zip(zip_bytes, target_dir)
    logger.info(f"Extracted {enc_file_path} to {target_dir}")
    

def run_enclave_project(client: Client):
    """
    Runs the enclave project with the given client.
    """
    running_dir = client.app_data(APP_NAME) / "jobs" / "running"
    done_dir = client.app_data(APP_NAME) / "jobs" / "done"
    output_dir = client.app_data(APP_NAME) / "jobs" / "outputs"
    # Iterates through each folder inside the running folder and looks for 
    # config.yaml file and code directory
    for folder in running_dir.iterdir():
        if folder.is_dir():
            config_file_path = folder / "config.yaml"
            code_dir = folder / "code"
            
            with open(config_file_path, "r") as f:
                config_file = yaml.safe_load(f)

            entrypoint = config_file.get("code",{}).get("entrypoint")
            if not entrypoint:
                logger.warning(f"Entrypoint not found in {config_file_path}")
                continue

            app_pvt_dir = get_app_private_data(client, APP_NAME)
            pvt_proj_dir = app_pvt_dir / folder.name
            pvt_proj_dir.mkdir(parents=True, exist_ok=True)
            proj_output_dir = output_dir / folder.name
            proj_output_dir.mkdir(parents=True, exist_ok=True)

            dataset_paths: list[Path] = get_dataset_path_from_config(config_file_path)

            
            dec_dataset_paths = [] # Decrypted dataset paths
            for dataset_path in dataset_paths:
                # Extract the encrypted data to the private project directory
                dec_dataset_path = pvt_proj_dir / dataset_path.name
                extract_enc_data(client, dataset_path, dec_dataset_path)
                dec_dataset_paths.append(dec_dataset_path)

            job_env = {"DATA_DIR" : ",".join(dec_dataset_paths),
                       "OUTPUT_DIR" : proj_output_dir/folder.name,
            }
            
            cmd = ["python3", code_dir / entrypoint]

            # Set up environment variables for direct Python execution
            env = os.environ.copy()
            env.update(job_env)


            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            # Wait for the process to finish
            process.wait()
            # Get the output and error messages
            output, error = process.communicate()
            logger.info(f"Output: {output}")
            logger.error(f"Error: {error}")
            # Move the folder to the done directory
            shutil.move(folder, done_dir / folder.name)



if __name__ == "__main__":

    client = Client.load()

    init_enclave(client)
    
    create_key_pair(client)

    while True:
        
        # Check if the enclave is ready to launch
        launch_enclave_project(client)

        # Run the Enclave Project
        run_enclave_project(client)

        sleep(3)
    

