"""Atlas | CLI Entry Point.

Provides a clean, terminal-friendly interface for running Atlas backups
without invoking the PyQt GUI.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import argparse
import sys

from atlas.backup.pipeline import Pipeline, PipelineResult

# =============================================================================
# FUNCTIONS
# =============================================================================


def clear_line():
    """Clear the current terminal line cross-platform."""
    if sys.stdout.isatty():
        sys.stdout.write("\r" + " " * 79 + "\r")
        sys.stdout.flush()


_LOGGED_MILESTONES = set()


def _on_progress(current, total):
    if total <= 0:
        return
    percent = int((current / total) * 100)
    text = "[Backup] Progress: {}% ({}/{} files)".format(percent, current, total)
    if sys.stdout.isatty():
        sys.stdout.write("\r{}".format(text[:78].ljust(78)))
        sys.stdout.flush()
    else:
        if percent % 10 == 0 and percent not in _LOGGED_MILESTONES:
            _LOGGED_MILESTONES.add(percent)
            print(text)


def _on_scanned(msg):
    if sys.stdout.isatty():
        text = "[Scanning] {}".format(msg[:67])
        sys.stdout.write("\r{}".format(text.ljust(78)))
        sys.stdout.flush()


def _on_estimated(size):
    clear_line()
    print("Estimated Backup Size: {}".format(size))
    if sys.stdout.isatty():
        print()


def _on_no_browsers():
    clear_line()
    print("Error: No supported browser profiles found on this system.")


def _on_disk_error(required, available):
    clear_line()
    print("Error: Insufficient disk space.")
    print("Required:  {}".format(required))
    print("Available: {}".format(available))


def run_cli(args=None):
    """Execute the backup pipeline in CLI mode.

    Args:
        args: Parsed command-line arguments for future expandability.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    from atlas.lib import browsers, permissions

    _LOGGED_MILESTONES.clear()

    if permissions.is_elevated():
        print("WARNING: Running with elevated privileges is not recommended.")

    if not browsers.verify_entries():
        print("Error: Failed to load browser configuration.")
        return 1

    print("========================================")
    print("             ATLAS CLI MODE             ")
    print("========================================")
    print("Starting backup process...\n")

    pipeline = Pipeline(
        progress_callback=_on_progress,
        scanned_callback=_on_scanned,
        estimated_callback=_on_estimated,
        no_browsers_found_callback=_on_no_browsers,
        disk_space_error_callback=_on_disk_error,
    )

    try:
        result = pipeline.run()
    except KeyboardInterrupt:
        pipeline.cancel()
        clear_line()
        print("\nBackup cancelled by user.")
        return 1
    except Exception as e:
        clear_line()
        print("\nAn unexpected error occurred: {}".format(e))
        return 1

    print()

    if result == PipelineResult.SUCCESS:
        print("========================================")
        print("Backup completed successfully.")
        print("========================================")
        return 0
    elif result == PipelineResult.CANCELLED:
        print("Backup was cancelled.")
        return 1
    elif result == PipelineResult.NO_BROWSERS_FOUND:
        return 1
    elif result == PipelineResult.INSUFFICIENT_DISK_SPACE:
        return 1
    else:
        print("Backup failed. Reason: {}".format(result.name))
        return 1
