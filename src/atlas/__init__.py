"""Atlas package root.

Provides compatibility initializations for Python 3.4 on Windows XP.
"""

import sys
import types

# Ensure 'typing' module exists for Python 3.4 standard library
try:
    import typing  # noqa: F401
except ImportError:
    class _TypingPlaceholder:
        def __getitem__(self, item):
            return self

        def __call__(self, *args, **kwargs):
            return self

        def __repr__(self):
            return "Any"

    _stub = types.ModuleType("typing")
    for _name in (
        "Any", "Callable", "Dict", "Generator", "Iterable",
        "List", "Mapping", "Optional", "Sequence", "Set",
        "Tuple", "Union", "TypeVar", "Generic", "cast"
    ):
        setattr(_stub, _name, _TypingPlaceholder())
    sys.modules["typing"] = _stub

# Ensure Path.mkdir supports exist_ok on Python 3.4
try:
    import inspect
    from pathlib import Path

    if "exist_ok" not in inspect.signature(Path.mkdir).parameters:
        _orig_path_mkdir = Path.mkdir

        def _compat_mkdir(self, mode=0o777, parents=False, exist_ok=False):
            try:
                _orig_path_mkdir(self, mode=mode, parents=parents)
            except OSError:
                if not (exist_ok and self.is_dir()):
                    raise

        Path.mkdir = _compat_mkdir
except Exception:
    pass
