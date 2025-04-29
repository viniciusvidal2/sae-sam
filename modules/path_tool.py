import sys
import os


def get_file_placement_path(relative_path: str) -> str:
    """Get the absolute path to the resource, works for dev and for PyInstaller.

    Args:
        relative_path (str): Relative path to the resource.

    Returns:
        str: Absolute path to the resource.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Normal script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
