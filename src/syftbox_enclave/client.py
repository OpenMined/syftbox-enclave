from pathlib import Path
import time
from typing import Any
import shutil
import yaml
from enum import Enum

from syft_core import Client, SyftBoxURL
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import SpinnerColumn, TextColumn
from rich.console import Group
from loguru import logger


from .utils import open_path_in_explorer

def connect(email: str):
    client = Client.load()

    enclave_datasite = client.datasites / email
    if not enclave_datasite.exists():
        raise ValueError(f"Enclave datasite {enclave_datasite} does not exist.")

    return EnclaveClient(email=email, client=client)
    
class DatasetStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"

class EnclaveClient(BaseModel):
    email: str
    client: Client

    class Config:
        arbitrary_types_allowed = True


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
        metrics = {}
        for dataset in datasets:
            host = SyftBoxURL(dataset.private).host
            dataset_id_str = str(dataset.uid)
            data_sources.append([host,dataset_id_str])
            metrics[dataset_id_str] = {
                "datasite" : host, 
                "status": DatasetStatus.PENDING.value,
            }

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
        
        metrics_path = enclave_proj_dir / 'metrics.yaml'
        with open(metrics_path, 'w') as f:
            yaml.dump(metrics, f)

        logger.info(f"Project {project_name} created in enclave app path {enclave_app_path}.")

        return EnclaveProject(client=self.client, email=self.email, project_name=project_name)



class EnclaveProject(BaseModel):

    client: Client
    email: str
    project_name: str

    class Config:
        arbitrary_types_allowed = True

    
    @property
    def output_dir(self) -> Path:
        enclave_app_path = self.client.app_data("enclave", datasite=self.email)
        return enclave_app_path / "jobs" / "outputs" / self.project_name
    
    @property
    def _metrics_path(self) -> Path:
        enclave_app_path = self.client.app_data("enclave", datasite=self.email)
        enclave_proj_dir = enclave_app_path / "jobs" / "launch" / self.project_name
        return enclave_proj_dir / 'metrics.yaml'

    def _get_metrics(self):
        metrics_path = self._metrics_path
        if not metrics_path.exists():
            logger.warning(f"Metrics file does not exist for "
                           + "\n project: {self.project_name}."
                           + "\n The project might have completed "
                           + "\n Kindly call .output() to check if the output is available.")
            return None
        with open(metrics_path, 'r') as f:
            return yaml.safe_load(f)

    def _render_table(self, metrics):
        table = Table()
        table.add_column("Dataset ID", style="cyan", no_wrap=True)
        table.add_column("Host", style="magenta")
        table.add_column("Status", style="bold")

        STATUS_EMOJI = {
            DatasetStatus.PENDING.value: '🟠',
            DatasetStatus.SUCCESS.value: '✅',
            DatasetStatus.ERROR.value: '❌',
        }

        for dataset_id, info in metrics.items():
            host = info.get('datasite', '-')
            status = info.get('status', '-')
            emoji = STATUS_EMOJI.get(status, '')
            table.add_row(dataset_id, host, f"{status} {emoji}".strip())
        
        return Group(
            Panel(f"[bold]Project:[/] {self.project_name}", border_style="blue"),
            table
        )

    def _all_success(self, metrics):
        return all(info.get('status') == DatasetStatus.SUCCESS.value for info in metrics.values())

    def status(self, block: bool = False) -> str:
        console = Console()
        metrics = self._get_metrics()

        if not metrics:
            if self.output_dir.exists():
                logger.info(f"Output already available for project {self.project_name} ✅"
                            + f"\n Directory: {self.output_dir}.")
                open_path_in_explorer(self.output_dir)
            else:
                logger.warning("Metrics not found and output is not available.")
            return "No metrics to display."

        if not block:
            console.print(self._render_table(metrics))
            return "Status displayed."

        try:
            with Live(self._render_table(metrics), console=console, screen=True, vertical_overflow="visible") as live:
                while not self._all_success(metrics):
                    time.sleep(2)
                    metrics = self._get_metrics()
                    if not metrics:
                        # This can happen if the job finishes and metrics.yaml is deleted.
                        break
                    live.update(self._render_table(metrics))
            
            console.print(f"\n[bold green]All datasets have uploaded to the Enclave! ✅[/bold green]")

        except KeyboardInterrupt:
            console.print("\nStatus monitoring interrupted.", style="bold yellow")
            return "Interrupted."
        
        return "All success."
        

    def output(self, block: bool = False):
        output_dir = self.output_dir

        if block:
            logger.info(f"Waiting for output for project {self.project_name}...", end="")
            while not output_dir.exists():
                print(".", end="", flush=True)
                time.sleep(2)
            print()  # Newline after waiting
            logger.info(f"Output available for project {self.project_name} ✅"
                        + f"\n Directory: {output_dir}.")
            open_path_in_explorer(output_dir)
            return output_dir
        else:
            if output_dir.exists():
                logger.info(f"Output available for project {self.project_name}"
                            + f"\n Directory: {output_dir}. ✅")
                open_path_in_explorer(output_dir)
                return output_dir
            else:
                logger.info(f"Output not yet available for project {self.project_name}. 🟠")




