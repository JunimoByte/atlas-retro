# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller spec for the Atlas Linux AppImage payload.

This spec intentionally builds *onedir*, not onefile.  The output is placed
directly in an AppImage-compatible AppDir at ``dist/Atlas.AppDir/usr/bin``.
AppImage tools can package that directory without first wrapping and then
extracting a PyInstaller one-file executable at every launch.

``noarchive=True`` also keeps pure Python modules as files in the onedir
payload rather than putting them into PyInstaller's compressed PYZ archive.
That trades a modestly larger AppImage for a simpler runtime layout with no
second application-level decompression layer.
"""

import importlib
import inspect
import os
import pkgutil

# =============================================================================
# QT BINDING DETECTION
# =============================================================================

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

print("appimage.spec: bundling %s, excluding %s" % (_active_qt, _excluded_qt))


# =============================================================================
# RESOURCES & CONFIGS
# =============================================================================

# Ensure 'src' is in sys.path
_base_dir = os.path.dirname(os.path.abspath(SPEC)) if "SPEC" in dir() else os.path.abspath(".")
if _base_dir not in sys.path:
    sys.path.insert(0, _base_dir)
_src_dir = os.path.join(_base_dir, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

datas = [
    ("assets/icons/*", "assets/icons"),
    ("assets/images/*", "assets/images"),
    ("configs/*", "configs"),
    ("pyproject.toml", "."),
]


# =============================================================================
# DYNAMIC HIDDEN IMPORTS
# =============================================================================


def collect_submodules(package_name):
    """Recursively collect every importable submodule in ``package_name``."""
    hidden = []
    try:
        package = importlib.import_module(package_name)
        for _, modname, _ in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            hidden.append(modname)
    except Exception as error:
        print(
            "Warning: failed to collect submodules for %s: %s" % (
                package_name, error
            )
        )
    return hidden


hiddenimports = (
    collect_submodules("atlas.backup")
    + collect_submodules("atlas.lib")
    + collect_submodules("atlas.display")
    + collect_submodules("atlas.ui")
)


# =============================================================================
# EXCLUDES
# =============================================================================

_unused_qt_modules = [
    "QtWebEngineWidgets", "QtWebEngineCore", "QtWebKit", "QtWebKitWidgets",
    "QtMultimedia", "QtNetwork", "QtNetworkAuth", "QtSql", "QtTest",
    "QtTextToSpeech", "QtWebSockets", "QtOpenGL", "QtSerialPort",
    "QtSensors", "QtNfc", "QtQuick", "QtQml", "Qt3DCore", "Qt3DRender",
    "Qt3DInput", "Qt3DLogic", "Qt3DExtras", "QtBluetooth", "QtPositioning",
    "QtPrintSupport", "QtQuickWidgets", "QtRemoteObjects", "QtSerialBus",
    "QtWebChannel",
]

_offline_module_prefixes = (
    "PyQt4.QtNetwork", "PyQt5.QtNetwork", "PyQt5.QtNetworkAuth",
    "PyQt5.QtWebEngine", "PyQt5.QtWebKit", "PyQt5.QtWebSockets",
    "PyQt5.QtBluetooth", "PyQt5.QtRemoteObjects", "PyQt5.QtWebChannel",
    "socket", "ssl", "http", "ftplib", "imaplib", "poplib",
    "smtplib", "telnetlib", "nntplib", "wsgiref",
)

_offline_binary_markers = (
    "QtWebEngine", "QtWebKit", "QtWebSockets", "Qt5Bluetooth",
    "Qt5RemoteObjects", "Qt5WebChannel",
)

_standard_library_excludes = [
    "tkinter", "unittest", "pytest", "doctest", "distutils", "setuptools",
    "pkg_resources",
    "email", "sqlite3", "concurrent", "http", "xml", "html", "pydoc",
    "socket", "ssl", "uuid", "pdb", "optparse", "getopt",
    "fractions", "decimal", "statistics", "hashlib", "hmac", "secrets",
    "ftplib", "imaplib", "poplib", "smtplib", "telnetlib", "nntplib", "cgi",
    "cgitb", "wsgiref", "mimetypes",
]

excludes_list = (
    _excluded_qt
    + [
        "%s.%s" % (binding, module)
        for binding in ("PyQt4", "PyQt5")
        for module in _unused_qt_modules
    ]
    + _standard_library_excludes
)


def enforce_offline_payload(analysis):
    """Fail the build if a blocked network-capable component is collected."""
    payload_paths = [entry[0] for entry in analysis.pure + analysis.binaries]

    def is_blocked_module(path):
        normalized_path = path.replace("\\", ".").replace("/", ".")
        return any(
            normalized_path == prefix
            or normalized_path.startswith(prefix + ".")
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
            "Offline packaging policy blocked: " + ", ".join(blocked)
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
    return cls(*args, **kwargs)


# =============================================================================
# APPIMAGE PAYLOAD
# =============================================================================

a = _safe_build(
    Analysis,
    ["src/atlas/main.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes_list,
    noarchive=True,
)

enforce_offline_payload(a)

pyz = PYZ(a.pure)

# Do not pass binaries or data files here: COLLECT writes those as normal
# files in the AppDir. Passing them to EXE would recreate a one-file payload.
exe = _safe_build(
    EXE,
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="atlas",
    debug=False,
    bootloader_ignore_signals=False,
    upx=False,
    console=False,
)

# COLLECT intentionally accepts only a basename and silently discards parent
# directories. Point its distpath at the AppDir's ``usr`` directory first, so
# the output lands at exactly ``dist/Atlas.AppDir/usr/bin/atlas``.
import PyInstaller.config  # noqa: E402
PyInstaller.config.CONF["distpath"] = os.path.join(
    PyInstaller.config.CONF["distpath"], "Atlas.AppDir", "usr"
)

# linuxdeploy/appimagetool expect the program below usr/bin in an AppDir.
coll = _safe_build(
    COLLECT,
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="bin",
)
