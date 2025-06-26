from pathlib import Path
import webbrowser



def open_path_in_explorer(path: str | Path):
    """
    Open a file or directory in the system's file explorer.
    
    Args:
        path (str | Path): The path to the file or directory to open.
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"The path {path} does not exist.")
    
    webbrowser.open(path.as_uri())