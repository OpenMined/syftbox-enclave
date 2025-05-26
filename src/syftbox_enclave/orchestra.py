import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional, TypeAlias, Union
import subprocess

from loguru import logger
from syft_core import Client as SyftBoxClient
from syft_core import SyftClientConfig

PathLike: TypeAlias = Union[str, os.PathLike, Path]

def setup_logger(level: str = "DEBUG") -> None:
    """
    Setup loguru logger with custom filtering.

    Args:
        level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove default handler
    logger.remove()

    # Add custom handler that filters out noisy logs
    logger.add(
        sys.stderr,
        level=level,
        filter=lambda record: "syft_event.server2" not in record["name"],
    )



def _prepare_root_dir(
    root_dir: Optional[PathLike] = None,
    reset: bool = False,
    key: str = "shared_client_dir",
) -> Path:
    if root_dir is None:
        return Path(tempfile.gettempdir(), key)

    root_path = Path(root_dir) / key

    if reset and root_path.exists():
        try:
            shutil.rmtree(root_path)
        except Exception as e:
            logger.warning(f"Failed to reset directory {root_path}: {e}")

    root_path.mkdir(parents=True, exist_ok=True)
    return root_path


def remove_enclave_stack_dir(
    key: str = "shared_client_dir", root_dir: Optional[PathLike] = None
) -> None:
    root_path = (
        Path(root_dir).resolve() / key if root_dir else Path(tempfile.gettempdir(), key)
    )

    if not root_path.exists():
        logger.warning(f"⚠️ Skipping removal, as path {root_path} does not exist")
        return None

    try:
        shutil.rmtree(root_path)
        logger.info(f"✅ Successfully removed directory {root_path}")
    except Exception as e:
        logger.error(f"❌ Failed to remove directory {root_path}: {e}")

class EnclaveStack:
    """An Enclave stack with a SyftBox client and a Enclave App"""

    def __init__(self, client: SyftBoxClient, root_dir: Path, **config_kwargs):
        self.client = client
        self.root_dir = root_dir
        self._start_enclave_app()

    def _start_enclave_app(self):
        main_file_path = Path(__file__).parent.parent.parent / "app" / "main.py"

        if not main_file_path.exists():
            raise FileNotFoundError(
                f"Main file {main_file_path} does not exist. Please check the path."
            )
        # Run the main.py file in a separate process to run parallel
        # to the current process
        env = os.environ.copy()
        env["SYFTBOX_CLIENT_CONFIG_PATH"] = str(self.client.config.path)
        log_file_path = Path(self.root_dir) / "logs" / f"{self.client.email}_enclave.log"
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Enclave log file: {log_file_path}")
        log_file = open(log_file_path, "a")
        self._enclave_process = subprocess.Popen(
            ["python", str(main_file_path)],
            stdout=log_file,
            stderr=log_file,
            env=env
        )
        self._log_file = log_file

    def init_session(self, host, **config_kwargs):
        pass

    def stop(self):
        if hasattr(self, "_enclave_process"):
            self._enclave_process.terminate()
            self._enclave_process.wait()
            if hasattr(self, "_log_file"):
                self._log_file.close()
            logger.info("Enclave process terminated.")
        else:
            logger.warning("No enclave process to terminate.")


def _get_syftbox_client(
    email: str,
    root_dir: PathLike,
) -> SyftBoxClient:
    """
    Get a SyftBox client for testing.

    Args:
        email (str): Email address of the user.
        root_dir (PathLike): Directory to store the client files.

    Returns:
        SyftBoxClient: The SyftBox client.
    """
    # We also save the config files in the root dir
    client_config = SyftClientConfig(
        email=email,
        client_url="http://localhost:5000",  # not used, just for local dev
        path=root_dir / f"{email}.config.json",
        data_dir=root_dir,
    ).save()
    return SyftBoxClient(client_config)


def setup_enclave_server(
    email: str,
    root_dir: Optional[PathLike] = None,
    reset: bool = False,
    key: str = "shared_client_dir",
    log_level: str = "DEBUG",
    **config_kwargs,
):
    # TODO: This works only with source github files
    # refactor the logic when releasing to pypi
    """
    Setup a mock Enclave server for testing.

    Args:
        email (str): Email address of the user.
        root_dir (Optional[PathLike]): Directory to store the server files.
        reset (bool): Whether to reset the directory.
        key (str): Key for the directory.
        log_level (str): Log level for logging.
        **config_kwargs: Additional configuration arguments.

    Returns:
        EnclaveStack: The Enclave stack with the client and the app
    """
    setup_logger(level=log_level)
    root_dir = _prepare_root_dir(root_dir, reset, key)

    client = _get_syftbox_client(email=email, root_dir=root_dir)

    logger.info(f"Launching mock Enclave server in {root_dir.resolve()}")

    return EnclaveStack(
        client=client,
        root_dir=root_dir,
        **config_kwargs,
    )