# rag_client.spec
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# --- Tiktoken fix ---
# tiktoken loads its encoding via a runtime plugin; PyInstaller needs explicit imports.
hidden_imports = [
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
]

# --- ChromaDB submodules (optional but safe) ---
hidden_imports += collect_submodules('chromadb')

# --- PyQt6 data files (optional) ---
datas = []
# datas += collect_data_files('PyQt6')  # uncomment if you have Qt resource files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RAG_Desktop_Client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # set True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # provide 'icon.ico' path if you have one
)