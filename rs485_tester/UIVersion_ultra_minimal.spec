# -*- mode: python ; coding: utf-8 -*-
"""
超極簡版本 - 最小化執行檔大小
"""

import sys
from PyInstaller.utils.hooks import collect_submodules

# 明確指定只需要的模組
needed_modules = [
    'tkinter',
    'tkinter.ttk', 
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'serial',
    'serial.tools.list_ports',
    'openpyxl',
]

# 大量排除不需要的模組
exclude_modules = [
    # 所有數值計算
    'numpy.*', 'scipy.*', 'pandas.*', 'matplotlib.*',
    'mkl.*', 'intel.*',
    
    # 所有機器學習
    'sklearn.*', 'tensorflow.*', 'torch.*', 'keras.*',
    
    # 所有圖像處理  
    'PIL.*', 'pillow.*', 'cv2.*', 'skimage.*',
    
    # 所有 Web 框架
    'flask.*', 'django.*', 'tornado.*', 'requests.*',
    'urllib3.*', 'certifi.*', 'chardet.*', 'idna.*',
    
    # XML/HTML 解析器
    'lxml.*', 'html5lib.*', 'beautifulsoup4.*',
    'defusedxml.*', 'xml.sax.*', 'xml.dom.*',
    
    # 開發和測試工具
    'pytest.*', 'unittest.*', 'doctest.*', 'test.*',
    'setuptools.*', 'distutils.*', 'pip.*',
    'sphinx.*', 'jupyter.*', 'ipython.*',
    
    # 編譯和構建工具
    'cython.*', 'numba.*', 'cffi.*', 'pycparser.*',
    
    # 不需要的標準庫模組
    'pdb', 'profile', 'cProfile', 'trace', 'timeit',
    'calendar', 'mailbox', 'mimetypes', 'quopri',
    'uu', 'base64', 'binhex', 'binascii',
    'difflib', 'gettext', 'locale',
    
    # 網路相關
    'ftplib', 'poplib', 'imaplib', 'smtplib',
    'telnetlib', 'socketserver', 'http.*',
    
    # 資料庫
    'sqlite3.*', 'dbm.*',
    
    # 壓縮
    'tarfile', 'zipfile', 'gzip', 'bz2', 'lzma',
    
    # 多媒體
    'wave', 'aifc', 'sunau', 'sndhdr',
    
    # 不需要的第三方
    'google.*', 'zope.*', 'sphinxcontrib.*',
    'ruamel.*', 'pytz.*', 'dateutil.*',
]

a = Analysis(
    ['UIVersion_minimal.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=needed_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=exclude_modules,
    noarchive=False,
    optimize=2,
)

# 手動過濾 - 更激進的排除
def should_exclude(name):
    """判斷是否應該排除模組"""
    exclude_patterns = [
        'numpy', 'scipy', 'pandas', 'matplotlib', 'sklearn',
        'PIL', 'cv2', 'tensorflow', 'torch', 'keras',
        'flask', 'django', 'requests', 'lxml', 'html5lib',
        'pytest', 'sphinx', 'jupyter', 'cython', 'numba',
        'google', 'zope', 'setuptools', 'distutils',
        'mkl', 'intel', 'cffi', 'cryptography',
        'defusedxml', 'ruamel', 'sphinxcontrib'
    ]
    
    name_lower = name.lower()
    return any(pattern in name_lower for pattern in exclude_patterns)

# 過濾純 Python 模組
a.pure = [x for x in a.pure if not should_exclude(x[0])]

# 過濾二進位檔案
a.binaries = [x for x in a.binaries if not should_exclude(x[0])]

# 過濾資料檔案
a.datas = [x for x in a.datas if not should_exclude(x[0])]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UIVersion_minimal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)