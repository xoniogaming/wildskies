"""The constellation figures were drafted here and are now in tools/sky_catalog.py (FIGURES, all 24, owner's yes
2026-11-12). This stays as the entry point for the contact sheet: tools/drafts/figures_sheet.py.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from sky_catalog import FIGURES  # noqa: E402

ALL = dict(FIGURES)
