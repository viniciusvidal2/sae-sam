# setup.py

from cx_Freeze import setup, Executable
import sys
import os

# Ensure application uses correct working directory
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # no console window (like console=False in PyInstaller)

# Include extra files (data folders)
include_files = [
    ('modules', 'modules'),
    ('windows', 'windows'),
    ('workers', 'workers'),
    ('resources', 'resources'),
    ('models', 'models'),
]

# Build options
build_exe_options = {
    'packages': [
        'vtkmodules', 'pyvistaqt', 'pyvista', 'open3d', 'transformers', 'pymavlink',
        'torch', 'ultralytics', 'onnx', 'onnxruntime', 'matplotlib', 'pyside6'
    ],
    'excludes': [
        'onnxscript',
        'torch._dynamo', 'torch._inductor', 'torch._inductor.codegen',
        'torch._inductor.kernel', 'torch._inductor.utils', 'torch._dynamo.optimizations',
        'torch._dynamo.eval_frame',
        'onnxscript.function_libs', 'onnxscript.function_libs.torch_aten', 'onnxscript.rewriter',
        'ultralytics.nn.modules', 'ultralytics.nn.tasks', 'ultralytics.engine.exporter',
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_cairo',
        'matplotlib.backends.backend_gtk3agg',
        'matplotlib.backends.backend_macosx',
        'matplotlib.backends.backend_pdf',
        'matplotlib.backends.backend_ps',
        'matplotlib.backends.backend_svg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_webagg',
    ],
    'include_files': include_files,
    'optimize': 2,  # optimization level 2 (bytecode)
    'zip_include_packages': ['*'],  # zip all included packages
    'zip_exclude_packages': [],     # do not exclude any
}

# Setup
setup(
    name="sae_sam",
    version="1.0",
    description="SAE SAM Project",
    options={"build_exe": build_exe_options},
    executables=[Executable("sae_sam.py", base=base, target_name="sae_sam.exe")]
)
