from pathlib import Path
import yaml
from io import BytesIO
from typing import Dict, List, Optional, Union
from zipfile import ZipFile

PathLike = Union[str, Path]


def validate_config_file(config_file_path: Path) -> bool:
    """
    Validates the config.yaml file
    """

    try:
        with open(config_file_path, "r") as f:
            config_file = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")

    required_keys = [
        "code",
        "data",
        "output",
    ]

    for key in required_keys:
        if key not in config_file:
            raise ValueError(f"Required key {key} is missing in config.yaml")

    return True



def extract_zip(zip_data: bytes, target_dir: PathLike) -> None:
    """Extract zip data to a target directory.

    Args:
        zip_data: Bytes containing zip content
        target_dir: Directory to extract files to
    """
    with ZipFile(BytesIO(zip_data)) as z:
        z.extractall(str(target_dir))


def zip_to_bytes(
    files_or_dirs: Union[PathLike, List[PathLike]], base_dir: Optional[PathLike] = None
) -> bytes:
    """Create a zip file from files or directories, returning the zip content as bytes.

    Args:
        files_or_dirs: Single path or list of paths to include
        base_dir: Optional base directory for relative paths in the zip

    Returns:
        Bytes containing the zip file
    """
    buffer = BytesIO()

    with ZipFile(buffer, "w") as z:
        paths = (
            [files_or_dirs] if isinstance(files_or_dirs, (str, Path)) else files_or_dirs
        )

        for path in paths:
            path = Path(path)

            if path.is_file():
                arcname = path.name if base_dir is None else path.relative_to(base_dir)
                z.write(path, arcname=str(arcname))
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        arcname = (
                            file_path.name
                            if base_dir is None
                            else file_path.relative_to(base_dir)
                        )
                        z.write(file_path, arcname=str(arcname))

    return buffer.getvalue()


def get_files_from_zip(zip_data: bytes) -> Dict[str, bytes]:
    """Extract files from zip data to a dictionary.

    Args:
        zip_data: Bytes containing zip content

    Returns:
        Dictionary mapping filenames to file contents
    """
    result = {}
    with ZipFile(BytesIO(zip_data)) as z:
        for filename in z.namelist():
            result[filename] = z.read(filename)

    return result