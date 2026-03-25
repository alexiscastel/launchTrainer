from pathlib import Path


_PKG_DIR = Path(__file__).resolve().parent
_SRC_PKG_DIR = _PKG_DIR.parent / "src" / "launchtrainer"

if _SRC_PKG_DIR.is_dir():
    __path__.append(str(_SRC_PKG_DIR))
