# sae_sam.spec
block_cipher = None

a = Analysis(
    ['sae_sam.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('modules/*', 'modules'),
        ('windows/*', 'windows'),
        ('workers/*', 'workers'),
        ('resources/*', 'resources'),
        ('models/**/*', 'models')
    ],
    hiddenimports=[
        'PIL.Image', 'PIL.ImageQt',
        'cv2', 'numpy', 'open3d', 'matplotlib', 'matplotlib.pyplot',
        'matplotlib.backends.backend_qt5agg',
        'pyvista', 'pyvistaqt', 'PySide6',
        'transformers', 'torch', 'ultralytics', 'onnx', 'onnxruntime',
        'utm', 'pymavlink'
    ],
    excludes=[
        'PyQt5', 'PyQt5.sip', 'PyQt6', 'PySide2',
        'tkinter',
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_cairo',
        'matplotlib.backends.backend_gtk3agg',
        'matplotlib.backends.backend_macosx',
        'matplotlib.backends.backend_pdf',
        'matplotlib.backends.backend_ps',
        'matplotlib.backends.backend_svg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_webagg',
        'torch._dynamo',
        'torch._inductor',
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
