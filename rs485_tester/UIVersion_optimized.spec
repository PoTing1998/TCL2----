# -*- mode: python ; coding: utf-8 -*-
"""
優化後的 PyInstaller 規格檔案，用於減少執行檔大小
"""

# 需要排除的大型模組
excluded_modules = [
    # 數值計算相關
    'numpy', 'scipy', 'pandas', 'matplotlib',
    'mkl', 'mkl._py_mkl_service', 'mkl._mklinit',
    
    # 圖像處理
    'PIL', 'pillow', 'cv2', 'skimage',
    
    # Web 相關
    'flask', 'django', 'requests', 'urllib3',
    'tornado', 'bottle', 'cherrypy',
    
    # 機器學習
    'sklearn', 'tensorflow', 'torch', 'keras',
    
    # 資料庫
    'sqlite3', 'pymongo', 'psycopg2', 'mysql',
    
    # 開發工具
    'pytest', 'sphinx', 'jupyter', 'ipython',
    'setuptools', 'distutils', 'pip',
    
    # XML/HTML 處理 (保留基本的)
    'lxml', 'beautifulsoup4', 'html5lib',
    
    # 其他大型模組
    'docutils', 'jinja2', 'markupsafe',
    'certifi', 'chardet', 'idna',
    'pytz', 'dateutil', 'six',
    'cryptography', 'cffi', 'pycparser',
    
    # Google/Zope 相關
    'google', 'zope', 'sphinxcontrib',
    
    # 測試相關
    'test', 'tests', 'testing',
    'unittest', 'doctest',
    
    # 不需要的 tkinter 模組
    'tkinter.test', 'tkinter.tix',
    
    # 編譯器相關
    'cython', 'numba',
]

# 只包含需要的模組
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'serial',
    'openpyxl',
    'threading',
    'socket',
    'datetime',
    'time',
    'os',
    'sys',
    'io',
]

a = Analysis(
    ['UIVersion.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 只包含必要的資料檔案
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    noarchive=False,
    optimize=2,  # 最高優化等級
)

# 過濾掉不需要的純 Python 模組
a.pure = [x for x in a.pure if not any(excluded in x[0] for excluded in excluded_modules)]

# 過濾掉不需要的二進位檔案
a.binaries = [x for x in a.binaries if not any(excluded in x[0] for excluded in excluded_modules)]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UIVersion_optimized',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,           # 移除除錯符號
    upx=True,            # 使用 UPX 壓縮
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # 不顯示控制台視窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,           # 可以添加圖示路徑
)