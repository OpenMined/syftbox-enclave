from pathlib import Path
import yaml


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