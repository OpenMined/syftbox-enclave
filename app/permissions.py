from pathlib import Path
import yaml
from typing import List


def add_permission_rule(path: str, pattern: str, read: List[str], write: List[str]):
    """
    Adds or updates a permission rule in syft.pub.yaml in the given path (must be a folder).
    If a rule with the same pattern exists, update only missing read/write entries (no duplicates).
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
    # Check for existing pattern
    for existing_rule in data["rules"]:
        if existing_rule.get("pattern") == pattern:
            # Update read and write lists, avoiding duplicates
            existing_access = existing_rule.setdefault("access", {})
            for key, new_values in [("read", read), ("write", write)]:
                existing = set(existing_access.get(key, []))
                updated = list(existing.union(new_values))
                existing_access[key] = updated
            break
    else:
        # No existing pattern, append new rule
        data["rules"].append(rule)
    with open(yaml_file, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
