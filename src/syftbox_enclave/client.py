from pathlib import Path
from typing import Any
from syft_core import Client, SyftBoxURL
from pydantic import BaseModel
import shutil
import yaml

def init_session(email: str):
    client = Client.load()

    return EnclaveClient(email=email, client=client)
    

class EnclaveClient(BaseModel):
    email: str
    client: Client


    def create_project(self,
                       project_name: str,
                       datasets: list[Any],
                       output_owners: list[str],
                       code_path: str | Path,
                       entrypoint: str | None = None):
        
        enclave_app_path = self.client.app_data("enclave", datasite=self.email)
        
        if not enclave_app_path.exists():
            raise ValueError(f"Enclave app path {enclave_app_path} does not exist.")
        
        enclave_launch_dir = enclave_app_path / "jobs" / "launch"
        enclave_proj_dir = enclave_launch_dir / project_name
        if enclave_proj_dir.exists():
            raise ValueError(f"Project {project_name} already exists in enclave app path.")
        enclave_proj_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle Data Sources
        data_sources = []
        for dataset in datasets:
            host = SyftBoxURL(dataset.private_path).host
            dataset_id = dataset.uid
            data_sources.append([host,dataset_id])

        # Handle Code Paths
        code_path = Path(code_path)
        code_dir = enclave_proj_dir / "code"
        code_dir.mkdir(parents=True, exist_ok=True)
        if code_path.is_dir():
            if entrypoint is None:
                raise ValueError("Entrypoint must be specified if code path is a directory.")
            # Copy only contents of code path to enclave project directory
            shutil.copytree(code_path, code_dir, dirs_exist_ok=True)
        else:
            entrypoint = code_path.name
            shutil.copy(code_path, code_dir)

        # Write config.yaml
        config = {
            'code': {'entrypoint': entrypoint},
            'data': data_sources,
            'output': output_owners
        }
        config_path = enclave_proj_dir / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)





