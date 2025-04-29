# hook-matplotlib.backends.py

from PyInstaller.utils.hooks import collect_submodules

# Prevent full backend scan (which causes disassembler crash)
hiddenimports = [
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backend_bases',
]

# override backend discovery completely
def get_matplotlib_backend():
    return ['matplotlib.backends.backend_qt5agg']