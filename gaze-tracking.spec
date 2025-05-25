# -*- mode: python ; coding: utf-8 -*-

datas=[
    ('/home/aml/py_workspace/facial_exp/venv/lib/python3.12/site-packages/mediapipe/modules/face_landmark/*.binarypb',
     'mediapipe/modules/face_landmark'),
     ('/home/aml/py_workspace/facial_exp/venv/lib/python3.12/site-packages/mediapipe/modules/face_detection/face_detection_short_range.tflite', 'mediapipe/modules/face_detection'),
    ('/home/aml/py_workspace/facial_exp/venv/lib/python3.12/site-packages/mediapipe/modules/face_landmark/face_landmark_with_attention.tflite', 'mediapipe/modules/face_landmark'),
]

binaries = [
    ('/usr/lib/x86_64-linux-gnu/libpython3.12.so.1.0', '.'),
]

a = Analysis(
    ['gaze-tracking.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
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
    name='gaze-tracking',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
