# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller spec file for Atlas on Windows XP."""

import importlib
import inspect
import os
import pkgutil
import struct
import sys

# Ensure 'src' is in sys.path so submodules can be imported and discovered
_base_dir = os.path.dirname(os.path.abspath(SPEC)) if "SPEC" in dir() else os.path.abspath(".")
_src_dir = os.path.join(_base_dir, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
if os.path.abspath("src") not in sys.path:
    sys.path.insert(0, os.path.abspath("src"))

from PyInstaller.building.build_main import EXE, PYZ, Analysis

# Detect Qt binding (PyQt4 preferred for Windows XP, PyQt5 fallback)
try:
    import PyQt4.QtCore  # noqa: F401
    _active_qt = "PyQt4"
    _excluded_qt = ["PyQt5", "PyQt6"]
except ImportError:
    try:
        import PyQt5.QtCore  # noqa: F401
        _active_qt = "PyQt5"
        _excluded_qt = ["PyQt4", "PyQt6"]
    except ImportError:
        raise RuntimeError("Atlas requires PyQt4 or PyQt5 to build.")

print("main.spec: bundling %s, excluding %s" % (_active_qt, _excluded_qt))

# Determine architecture: x86 (32-bit, typical for XP) or x86_64
_target_arch = "x86_64" if struct.calcsize("P") == 8 else "x86"
_portable_name = "Atlas-%s-Portable" % _target_arch

print("main.spec: creating %s" % _portable_name)

datas = [
    ('assets/icons/*', 'assets/icons'),
    ('assets/images/*', 'assets/images'),
    ('configs/*', 'configs'),
    ('pyproject.toml', '.'),
]


def collect_submodules(package_name):
    """Recursively collect all submodules in a package for hiddenimports."""
    hidden = []
    try:
        package = importlib.import_module(package_name)
        for _, modname, _ in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            hidden.append(modname)
    except Exception as error:
        print("Warning: failed to collect submodules for %s: %s" % (package_name, error))
    return hidden


hiddenimports = (
    collect_submodules("atlas.backup")
    + collect_submodules("atlas.lib")
    + collect_submodules("atlas.display")
    + collect_submodules("atlas.ui")
)

_unused_qt_modules = [
    'QtWebEngineWidgets', 'QtWebEngineCore', 'QtWebKit', 'QtWebKitWidgets',
    'QtMultimedia', 'QtNetwork', 'QtNetworkAuth', 'QtSql', 'QtTest',
    'QtTextToSpeech', 'QtWebSockets', 'QtOpenGL', 'QtSerialPort',
    'QtSensors', 'QtNfc', 'QtQuick', 'QtQml', 'Qt3DCore', 'Qt3DRender',
    'Qt3DInput', 'Qt3DLogic', 'Qt3DExtras', 'QtBluetooth', 'QtPositioning',
    'QtPrintSupport', 'QtQuickWidgets', 'QtRemoteObjects', 'QtSerialBus',
    'QtWebChannel',
]

_offline_module_prefixes = (
    'PyQt4.QtNetwork', 'PyQt4.QtWebKit',
    'PyQt5.QtNetwork', 'PyQt5.QtNetworkAuth', 'PyQt5.QtWebEngine',
    'PyQt5.QtWebKit', 'PyQt5.QtWebSockets', 'PyQt5.QtBluetooth',
    'PyQt6.QtNetwork', 'PyQt6.QtNetworkAuth', 'PyQt6.QtWebEngine',
    'socket', 'ssl', 'http', 'ftplib', 'imaplib', 'poplib',
    'smtplib', 'telnetlib', 'nntplib', 'wsgiref',
)

_offline_binary_markers = (
    'QtWebEngine', 'QtWebKit', 'QtWebSockets', 'QtNetwork',
)

_standard_library_excludes = [
    'tkinter', 'unittest', 'pytest', 'doctest', 'distutils', 'setuptools',
    'pkg_resources',
    'email', 'sqlite3', 'concurrent', 'http', 'xml', 'html', 'pydoc',
    'socket', 'ssl', 'uuid', 'pdb', 'optparse', 'getopt',
    'fractions', 'decimal', 'statistics', 'hashlib', 'hmac', 'secrets',
    'ftplib', 'imaplib', 'poplib', 'smtplib', 'telnetlib', 'nntplib', 'cgi',
    'cgitb', 'wsgiref', 'mimetypes',
]

excludes_list = (
    _excluded_qt
    + [
        "%s.%s" % (binding, module)
        for binding in ('PyQt4', 'PyQt5', 'PyQt6')
        for module in _unused_qt_modules
    ]
    + _standard_library_excludes
)


def enforce_offline_payload(analysis):
    """Fail the build if a blocked network-capable component is collected."""
    payload_paths = [entry[0] for entry in analysis.pure + analysis.binaries]

    def is_blocked_module(path):
        normalized_path = path.replace('\\', '.').replace('/', '.')
        return any(
            normalized_path == prefix
            or normalized_path.startswith(prefix + '.')
            for prefix in _offline_module_prefixes
        )

    blocked_modules = sorted(
        path for path in payload_paths if is_blocked_module(path)
    )
    blocked_payload = sorted(
        path for path in payload_paths
        if any(marker.lower() in path.lower()
               for marker in _offline_binary_markers)
    )
    if blocked_modules or blocked_payload:
        blocked = blocked_modules + blocked_payload
        raise SystemExit(
            'Offline packaging policy blocked: ' + ', '.join(blocked)
        )


def _safe_build(cls, *args, **kwargs):
    """Filter kwargs to those accepted by the running PyInstaller version."""
    try:
        sig = inspect.signature(cls.__init__)
        accepted = set(sig.parameters.keys())
        has_varkw = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        )
        if not has_varkw:
            kwargs = dict((k, v) for k, v in kwargs.items() if k in accepted)
    except Exception:
        pass
    if cls.__name__ == 'EXE':
        try:
            import PyInstaller
            ver_major = int(PyInstaller.__version__.split('.')[0])
            if ver_major < 4:
                py3_allowed = set([
                    'name', 'debug', 'strip', 'upx', 'console', 'icon',
                    'version', 'uac_admin', 'uac_uiaccess', 'runtime_tmpdir'
                ])
                kwargs = dict((k, v) for k, v in kwargs.items() if k in py3_allowed)
        except Exception:
            pass
    return cls(*args, **kwargs)


a = _safe_build(
    Analysis,
    ['src/atlas/main.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes_list,
    noarchive=False,
)

enforce_offline_payload(a)

pyz = PYZ(a.pure)

_icon = 'assets/icons/Icon.ico' if sys.platform == 'win32' else None

exe = _safe_build(
    EXE,
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=_portable_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    icon=_icon,
)
