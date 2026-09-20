# 1. Programming Language: Python
Date: 2026-02-18

## Context
Atlas requires a reliable foundation to perform sensitive file system operations across multiple operating systems, while remaining easy to maintain, review, and audit.

## Decision
I chose **Python** as the core programming language.

## Rationale
- **Safety & Stability**: Python provides automatic memory management and structured exception handling, reducing the risk of crashes or undefined behavior during backup operations.
- **Cross-platform Capabilities**: Python's standard library offers consistent abstractions for filesystem access (e.g., `pathlib`, `os`), enabling predictable behavior on Windows and Linux.
- **Legacy Compatibility (Python 3.4)**: Python 3.4.4 is the final official Python release that runs natively on Windows XP SP3. Adopting a Python 3.4 baseline allows Atlas to support vintage hardware while retaining modern Python 3 foundations.
- **Maintainability**: Python's readability lowers the barrier for long-term maintenance, code reviews, and external contributions.
- **Performance**: For this domain, performance bottlenecks are disk-bound, not CPU-bound, so Python's overhead is negligible.
