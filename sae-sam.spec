# sae_sam.spec
block_cipher = None

a = Analysis(
    ['sae_sam.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('modules/*', 'modules'),
        ('pingmapper/*', 'pingmapper'),
        ('windows/*', 'windows'),
        ('workers/*', 'workers'),
        ('resources/*', 'resources'),
        ('models/distill_any_depth/22c685bb9cd0d99520f2438644d2a9ad2cea41dc/*', 'models/distill_any_depth/22c685bb9cd0d99520f2438644d2a9ad2cea41dc'),
        ('models/image_segmentation/args.yaml', 'models/image_segmentation'),
        ('models/image_segmentation/weights/best.pt', 'models/image_segmentation/weights')
    ],
    hiddenimports=[
        'PIL.Image', 'PIL.ImageQt',
        'cv2', 'numpy', 'open3d', 'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_qt5agg',
        'pyvista', 'pyvistaqt', 'PySide6',
        'transformers', 'torch', 'ultralytics', 'onnx', 'onnxruntime',
        'utm', 'pymavlink',
        'vtkmodules', 'vtkmodules.all', 'vtkmodules.util', 'vtkmodules.util.data_model', 'vtkmodules.util.execution_model',
        'torch._inductor', 'torch._dynamo'
    ],
    excludes=[
        'PyQt5', 'PyQt5.sip', 'PyQt6', 'PySide2',
        'tkinter',
        'matplotlib.backends.backend_cairo',
        'matplotlib.backends.backend_gtk3agg',
        'matplotlib.backends.backend_macosx',
        'matplotlib.backends.backend_pdf',
        'matplotlib.backends.backend_ps',
        'matplotlib.backends.backend_svg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_webagg',
        'onnxscript'
    ],
    hookspath=['.'],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=True,
    name='sae_sam',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='resources/saesam_icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sae_sam'
)
