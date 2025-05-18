from pathlib import Path
import yaml


def validate_config_file(config_file: Path) -> bool:
    """
    Validates the config.yaml file
    """

    try:
        with open(fl_config, "r") as f:
            fl_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")

    required_keys = [
        "code",
        "data",
        "output",
    ]

    for key in required_keys:
        if key not in fl_config:
            raise ValueError(f"Required key {key} is missing in fl_config.json")

    return True