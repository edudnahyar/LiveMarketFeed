"""
theme.py — central palette / fonts / global stylesheet for the
"Market Cyberdeck" dashboard.

Everything visual (colors, fonts, spacing) is defined here so the
look can be re-tuned from one place without touching widget code.
"""

from PySide6.QtGui import QColor, QFont, QFontDatabase


# ---------------------------------------------------------------------------
# Palette — near-black base with cyan / amber HUD accents, matching the
# "smart-ops-center" reference (dark bg, thin neon borders, warm/cool accents)
# ---------------------------------------------------------------------------

BG_APP        = "#03050a"   # window background
BG_PANEL      = "#070b12"   # panel fill
BG_PANEL_ALT  = "#0b1119"   # slightly lighter panel (headers, rows)
BORDER_DIM    = "#16202b"   # inactive panel border / grid lines
GRID_LINE     = "#0d141c"   # background grid dots/lines

ACCENT_CYAN   = "#3fe3d0"   # primary accent — borders, headings, primary series
ACCENT_CYAN_DIM = "#1f6f68"
ACCENT_AMBER  = "#ffa73b"   # secondary accent — highlights, warnings, 2nd series
ACCENT_RED    = "#ff4d5e"   # negative change / alerts
ACCENT_GREEN  = "#33e28a"   # positive change
ACCENT_BLUE   = "#4da3ff"   # tertiary series

TEXT_PRIMARY  = "#dceaf2"
TEXT_MUTED    = "#5c7488"
TEXT_DIM      = "#3a4b58"

# Convenience QColor objects for use inside paintEvents
Q_BG_PANEL      = QColor(BG_PANEL)
Q_BORDER_DIM    = QColor(BORDER_DIM)
Q_GRID_LINE     = QColor(GRID_LINE)
Q_ACCENT_CYAN   = QColor(ACCENT_CYAN)
Q_ACCENT_AMBER  = QColor(ACCENT_AMBER)
Q_ACCENT_RED    = QColor(ACCENT_RED)
Q_ACCENT_GREEN  = QColor(ACCENT_GREEN)
Q_TEXT_PRIMARY  = QColor(TEXT_PRIMARY)
Q_TEXT_MUTED    = QColor(TEXT_MUTED)


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
# These are sane cross-platform fallbacks. If you want an exact match to the
# reference image, drop TTFs for a display face (e.g. "Rajdhani", "Orbitron")
# and a mono face (e.g. "Share Tech Mono") into gui/assets/fonts/ and call
# load_bundled_fonts() before building the window — see bottom of this file.

FONT_DISPLAY = "Rajdhani, Segoe UI, Arial, sans-serif"
FONT_MONO = "Share Tech Mono, Consolas, DejaVu Sans Mono, monospace"


def spaced(text: str, gap: str = " ") -> str:
    """HUD titles are letter-spaced. Qt Style Sheets don't support the CSS
    letter-spacing property reliably, so we fake it by inserting spaces."""
    return gap.join(list(text.upper()))


def load_bundled_fonts(asset_dir: str = None):
    """Optionally load bundled font files so headings/numbers render in a
    proper HUD typeface instead of the OS default. Safe no-op if the
    directory/files don't exist."""
    import os
    if asset_dir is None:
        asset_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
    if not os.path.isdir(asset_dir):
        return
    for fname in os.listdir(asset_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            QFontDatabase.addApplicationFont(os.path.join(asset_dir, fname))


def mono_font(point_size: int = 10, bold: bool = False) -> QFont:
    f = QFont("Share Tech Mono")
    if "Share Tech Mono" not in QFontDatabase.families():
        f = QFont("Consolas")
        if "Consolas" not in QFontDatabase.families():
            f = QFont("Monospace")
            f.setStyleHint(QFont.Monospace)
    f.setPointSize(point_size)
    f.setBold(bold)
    return f


def display_font(point_size: int = 11, bold: bool = True) -> QFont:
    f = QFont("Rajdhani")
    if "Rajdhani" not in QFontDatabase.families():
        f = QFont("Segoe UI")
    f.setPointSize(point_size)
    f.setBold(bold)
    return f


# ---------------------------------------------------------------------------
# Global stylesheet — base widget look. Panel-specific chrome (borders,
# corner brackets) is hand-painted in gui/Widgets/frame.py since QSS can't
# draw HUD-style corner brackets or glow.
# ---------------------------------------------------------------------------

GLOBAL_QSS = f"""
QWidget {{
    background-color: {BG_APP};
    color: {TEXT_PRIMARY};
    font-family: {FONT_DISPLAY};
}}

QLabel {{
    background: transparent;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 8px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_DIM};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_CYAN_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QToolTip {{
    background-color: {BG_PANEL_ALT};
    color: {ACCENT_CYAN};
    border: 1px solid {ACCENT_CYAN};
    padding: 4px;
}}
"""
