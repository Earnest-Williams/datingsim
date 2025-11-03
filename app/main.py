"""Application entry point."""

import argparse
import sys


def _ensure_supported_runtime():
    """Fail fast with a helpful message when executed on Python 2."""

    if sys.version_info[0] < 3:
        raise SystemExit(
            "This application requires Python 3. "
            "Please run it with `python3 -m app.main`."
        )


def _import_qt_objects():
    """Import Qt classes with a friendlier error message on failure."""

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        raise SystemExit(
            "PySide6 is not available. Install it (e.g. `pip install PySide6`) "
            "before launching the application."
        )

    from app.gui.main_window import MainWindow

    return QApplication, MainWindow


def _exec_qt_application(qt_args, seed=None):
    """Initialise and run the Qt application."""

    QApplication, MainWindow = _import_qt_objects()

    qt_app = QApplication([sys.argv[0], *qt_args])
    win = MainWindow(seed=seed)
    win.show()

    exec_method = getattr(qt_app, "exec", None) or getattr(qt_app, "exec_", None)
    if exec_method is None:
        raise AttributeError("Qt application object exposes neither exec nor exec_.")

    return exec_method()


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Launch the dating sim UI.")
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed the game for deterministic behaviour.",
    )
    return parser.parse_known_args(argv)


def main(argv=None):
    _ensure_supported_runtime()
    argv = sys.argv[1:] if argv is None else argv
    args, qt_args = _parse_args(argv)
    sys.exit(_exec_qt_application(qt_args, seed=args.seed))


if __name__ == "__main__":
    main()
