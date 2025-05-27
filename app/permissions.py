import yaml
from typing import List
from pathlib import Path


def add_permission_rule(path: str, pattern: str, read: List[str], write: List[str]):
    """
    Adds a permission rule to syft.pub.yaml in the given path (must be a folder).
    If the file does not exist, it creates it. If it exists, it appends the rule.
    Raises ValueError if path is not a directory.
    """
    folder = Path(path)
    if not folder.is_dir():
        raise ValueError(f"Provided path '{path}' is not a directory.")
    yaml_file = folder / "syft.pub.yaml"
    rule = {
        "pattern": pattern,
        "access": {
            "read": read,
            "write": write
        }
    }
    if yaml_file.exists():
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    if "rules" not in data or not isinstance(data["rules"], list):
        data["rules"] = []
    data["rules"].append(rule)
    with open(yaml_file, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
