"""
Design Tokens — Standard El-Joumla ERP
World-class dark theme with gold accents for Arabic business
"""
from dataclasses import dataclass, field
from typing import Dict

@dataclass(frozen=True)
class Colors:
    # ── Backgrounds (3-level depth) ──
    BG_VOID: str = "#08090d"          # Deepest background
    BG_PRIMARY: str = "#0f1117"       # Main surface (sidebar, titlebar)
    BG_SECONDARY: str = "#161822"     # Cards, panels, dialogs
    BG_TERTIARY: str = "#1e2030"      # Raised elements, inputs
    BG_HOVER: str = "#252840"         # Hover states
    BG_ACTIVE: str = "#2a2d4a"        # Active/pressed states
    BG_OVERLAY: str = "rgba(0,0,0,0.6)"  # Modal overlays

    # ── Borders ──
    BORDER_DEFAULT: str = "#2a2d45"
    BORDER_SUBTLE: str = "#1e2035"
    BORDER_FOCUS: str = "#d4a853"     # Gold focus ring
    BORDER_HOVER: str = "#3d4166"

    # ── Text ──
    TEXT_PRIMARY: str = "#f0f0f5"
    TEXT_SECONDARY: str = "#9496b0"
    TEXT_MUTED: str = "#5d5f7a"
    TEXT_INVERSE: str = "#0f1117"
    TEXT_GOLD: str = "#d4a853"
    TEXT_LINK: str = "#6c9cef"

    # ── Brand / Accent ──
    ACCENT_GOLD: str = "#d4a853"      # Primary accent (culturally significant)
    ACCENT_GOLD_LIGHT: str = "#e8c878"
    ACCENT_GOLD_DARK: str = "#b8923f"
    ACCENT_GOLD_SUBTLE: str = "rgba(212,168,83,0.12)"
    ACCENT_BLUE: str = "#6c9cef"      # Secondary accent
    ACCENT_TEAL: str = "#2d8c6f"      # Success/positive

    # ── Semantic ──
    SUCCESS: str = "#2d8c6f"
    SUCCESS_BG: str = "rgba(45,140,111,0.12)"
    WARNING: str = "#e8a838"
    WARNING_BG: str = "rgba(232,168,56,0.12)"
    ERROR: str = "#e85454"
    ERROR_BG: str = "rgba(232,84,84,0.12)"
    INFO: str = "#6c9cef"
    INFO_BG: str = "rgba(108,156,239,0.12)"

    # ── Gold Gradient ──
    GOLD_GRADIENT_START: str = "#d4a853"
    GOLD_GRADIENT_END: str = "#e8c878"

@dataclass(frozen=True)
class Spacing:
    XS: int = 4
    SM: int = 8
    MD: int = 12
    LG: int = 16
    XL: int = 24
    XXL: int = 32
    XXXL: int = 48

@dataclass(frozen=True)
class Radius:
    SM: str = "6px"
    MD: str = "10px"
    LG: str = "14px"
    XL: str = "18px"
    FULL: str = "9999px"

@dataclass(frozen=True)
class Typography:
    FONT_FAMILY: str = "'Cairo', 'Segoe UI', 'Roboto', sans-serif"
    FONT_FAMILY_MONO: str = "'JetBrains Mono', 'Fira Code', monospace"
    SIZE_XS: str = "11px"
    SIZE_SM: str = "12px"
    SIZE_MD: str = "14px"
    SIZE_LG: str = "16px"
    SIZE_XL: str = "20px"
    SIZE_XXL: str = "24px"
    SIZE_HERO: str = "32px"
    WEIGHT_NORMAL: str = "400"
    WEIGHT_MEDIUM: str = "500"
    WEIGHT_SEMIBOLD: str = "600"
    WEIGHT_BOLD: str = "700"
    WEIGHT_BLACK: str = "800"
    LINE_HEIGHT_TIGHT: str = "1.3"
    LINE_HEIGHT_NORMAL: str = "1.6"
    LINE_HEIGHT_RELAXED: str = "1.8"

@dataclass(frozen=True)
class Shadows:
    SM: str = "0 2px 8px rgba(0,0,0,0.3)"
    MD: str = "0 4px 16px rgba(0,0,0,0.4)"
    LG: str = "0 8px 32px rgba(0,0,0,0.5)"
    XL: str = "0 16px 48px rgba(0,0,0,0.6)"
    GOLD_GLOW: str = "0 0 20px rgba(212,168,83,0.15)"
    GOLD_GLOW_STRONG: str = "0 0 30px rgba(212,168,83,0.25)"

@dataclass(frozen=True)
class Transitions:
    FAST: str = "150ms ease"
    NORMAL: str = "250ms ease"
    SLOW: str = "400ms ease"
    BOUNCE: str = "300ms cubic-bezier(0.34, 1.56, 0.64, 1)"

# Singleton instances
C = Colors()
S = Spacing()
R = Radius()
T = Typography()
SH = Shadows()
TR = Transitions()

def qss(name: str, **overrides) -> str:
    """Generate QSS with token values. Usage: qss('QPushButton', background=C.BG_TERTIARY)"""
    # Convert snake_case to kebab-case for QSS properties
    def to_kebab(s):
        import re
        return re.sub(r'_([a-z])', lambda m: '-' + m.group(1), s).replace('_', '-')

    props = []
    for k, v in overrides.items():
        if v is not None:
            props.append(f"  {to_kebab(k)}: {v};")

    return f"{name} {{\n" + "\n".join(props) + "\n}}"