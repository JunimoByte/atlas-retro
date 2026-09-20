# 2. GUI Framework: PyQt (Qt)
Date: 2026-02-18

## Context
Atlas requires a graphical user interface that is professional, responsive, and visually consistent across all supported platforms without maintaining separate UI implementations.

## Decision
I selected **PyQt** (targeting **PyQt4** / Qt 4.8 for Windows XP, with runtime shims supporting PyQt5 as a fallback).

## Rationale
- **Maturity**: Qt is a long-established, production-proven framework with exceptional stability and backward compatibility.
- **Native Look and Feel**: Qt 4 integrates seamlessly with native Windows XP visual styles (Luna and Classic) without requiring resource-intensive DWM effects.
- **Cross-Version Architecture**: By abstracting Qt access through `atlas.compatibility.qt`, the application runs natively against PyQt4 on Windows XP while remaining compatible with PyQt5 on modern environments.
- **Comprehensive Widget Set**: Qt provides a rich collection of high-quality widgets, eliminating custom UI overhead.
