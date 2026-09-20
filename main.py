#!/usr/bin/env python3
"""Atlas | Root Entry Point.

Allows running Atlas directly from the repository root:
    python3 main.py
    ./main.py
    python3 main.py --cli
"""

import os
import sys

# Ensure 'src' is first in sys.path for direct checkout execution
_base_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_base_dir, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from atlas.main import main  # noqa: E402

if __name__ == "__main__":
    main()
