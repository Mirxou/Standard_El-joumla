"""
Design Tokens — Standard El-Joumla ERP
╔══════════════════════════════════════════════════════╗
║  OBSIDIAN LUXE v3.0 — World-Class Arabic ERP Theme ║
║  Deep obsidian + Rose Gold + Amber accents          ║
║  Designed for financial excellence & visual luxury   ║
╚══════════════════════════════════════════════════════╝
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    """
    Obsidian Luxe — 4-layer depth system with warm metallic accents.
    Each layer has subtle blue undertones for professional depth.
    """
    # ── Backgrounds (5-layer depth architecture) ──────────────────────
    BG_VOID: str = "#050507"            # Deepest void — window frame, outer space
    BG_ABYSS: str = "#0a0b10"           # Abyss — outermost app surface
    BG_PRIMARY: str = "#0e1018"         # Primary — sidebar, titlebar, main surfaces
    BG_SECONDARY: str = "#141724"       # Secondary — cards, panels, dialogs, content areas
    BG_TERTIARY: str = "#1c2033"        # Tertiary — inputs, raised elements, embedded areas
    BG_ELEVATED: str = "#232841"        # Elevated — popovers, dropdowns, tooltips
    BG_HOVER: str = "#2a3052"           # Hover — interactive hover states
    BG_ACTIVE: str = "#313866"          # Active — pressed/selected states
    BG_OVERLAY: str = "rgba(5,5,7,0.75)"  # Overlay — modal/dialog backdrop
    BG_GLASS: str = "rgba(20,23,36,0.85)"  # Glass — frosted glass effect base

    # ── Borders (3-level hierarchy) ───────────────────────────────────
    BORDER_VOID: str = "#0e1018"        # Invisible border — structural separation
    BORDER_SUBTLE: str = "#1c2033"      # Subtle — between siblings
    BORDER_DEFAULT: str = "#282d48"     # Default — standard element borders
    BORDER_MEDIUM: str = "#363d5e"      # Medium — emphasized sections
    BORDER_HOVER: str = "#4a5280"       # Hover — interactive border response
    BORDER_FOCUS: str = "#c9956b"       # Focus — rose gold focus ring
    BORDER_GOLD_GLOW: str = "#d4a853"   # Gold glow — premium focus

    # ── Text (5-level hierarchy for perfect readability) ──────────────
    TEXT_BRIGHT: str = "#ffffff"         # Bright — headlines, key data, CTAs
    TEXT_PRIMARY: str = "#e8eaf0"        # Primary — body text, paragraphs
    TEXT_SECONDARY: str = "#9498b8"      # Secondary — descriptions, meta text
    TEXT_MUTED: str = "#5d6184"          # Muted — placeholders, hints, timestamps
    TEXT_GHOST: str = "#363a56"          # Ghost — disabled text, watermarks
    TEXT_INVERSE: str = "#0e1018"        # Inverse — text on gold/accent backgrounds

    # ── Brand Accents (Rose Gold + Amber + Teal) ─────────────────────
    ACCENT_ROSE: str = "#c9956b"         # Rose Gold — primary accent (unique, luxurious)
    ACCENT_ROSE_LIGHT: str = "#e0b896"   # Rose Gold Light — hover states
    ACCENT_ROSE_DARK: str = "#a67a52"    # Rose Gold Dark — pressed states
    ACCENT_ROSE_SUBTLE: str = "rgba(201,149,107,0.10)"  # Rose Gold subtle bg
    ACCENT_ROSE_GLOW: str = "rgba(201,149,107,0.25)"    # Rose Gold glow effect

    ACCENT_AMBER: str = "#d4a853"        # Amber Gold — secondary accent, financial
    ACCENT_AMBER_LIGHT: str = "#e8c878"  # Amber Gold Light
    ACCENT_AMBER_DARK: str = "#b8923f"   # Amber Gold Dark
    ACCENT_AMBER_SUBTLE: str = "rgba(212,168,83,0.10)"  # Amber subtle bg

    ACCENT_TEAL: str = "#3db89c"         # Teal — success, positive, growth
    ACCENT_TEAL_LIGHT: str = "#5dd4b6"   # Teal Light
    ACCENT_TEAL_DARK: str = "#2a9a7e"    # Teal Dark
    ACCENT_TEAL_SUBTLE: str = "rgba(61,184,156,0.10)"

    ACCENT_BLUE: str = "#6b8cd4"         # Blue — info, links, secondary actions
    ACCENT_BLUE_LIGHT: str = "#8da8e8"   # Blue Light
    ACCENT_BLUE_SUBTLE: str = "rgba(107,140,212,0.10)"

    # ── Semantic Colors ──────────────────────────────────────────────
    SUCCESS: str = "#3db89c"
    SUCCESS_BG: str = "rgba(61,184,156,0.10)"
    SUCCESS_BORDER: str = "rgba(61,184,156,0.30)"

    WARNING: str = "#e0a040"
    WARNING_BG: str = "rgba(224,160,64,0.10)"
    WARNING_BORDER: str = "rgba(224,160,64,0.30)"

    ERROR: str = "#e05555"
    ERROR_BG: str = "rgba(224,85,85,0.10)"
    ERROR_BORDER: str = "rgba(224,85,85,0.30)"

    INFO: str = "#6b8cd4"
    INFO_BG: str = "rgba(107,140,212,0.10)"
    INFO_BORDER: str = "rgba(107,140,212,0.30)"

    # ── Gradient Presets ─────────────────────────────────────────────
    GRADIENT_ROSE: str = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #c9956b,stop:1 #e0b896)"
    GRADIENT_AMBER: str = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #d4a853,stop:1 #e8c878)"
    GRADIENT_TEAL: str = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2a9a7e,stop:1 #5dd4b6)"
    GRADIENT_DARK: str = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #141724,stop:1 #0e1018)"
    GRADIENT_SURFACE: str = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1c2033,stop:0.5 #141724,stop:1 #0e1018)"
    GRADIENT_HERO: str = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #c9956b,stop:0.3 #d4a853,stop:0.7 #e0b896,stop:1 #e8c878)"


@dataclass(frozen=True)
class Spacing:
    """8px grid system for consistent spacing."""
    XXXS: int = 2
    XXS: int = 4
    XS: int = 8
    SM: int = 12
    MD: int = 16
    LG: int = 20
    XL: int = 24
    XXL: int = 32
    XXXL: int = 40
    MEGA: int = 48
    ULTRA: int = 64


@dataclass(frozen=True)
class Radius:
    """Multi-tier radius system for visual hierarchy."""
    XS: str = "4px"
    SM: str = "6px"
    MD: str = "8px"
    LG: str = "12px"
    XL: str = "16px"
    XXL: str = "20px"
    FULL: str = "9999px"


@dataclass(frozen=True)
class Typography:
    """Arabic-first typography with Cairo as primary font."""
    FONT_FAMILY: str = "'Cairo', 'Noto Sans Arabic', 'Segoe UI', system-ui, sans-serif"
    FONT_FAMILY_DISPLAY: str = "'Cairo', 'Noto Sans Arabic', sans-serif"
    FONT_FAMILY_MONO: str = "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace"
    FONT_FAMILY_NUMBERS: str = "'Tabular Nums', 'Cairo', monospace"

    SIZE_2XS: str = "10px"
    SIZE_XS: str = "11px"
    SIZE_SM: str = "12px"
    SIZE_MD: str = "13px"
    SIZE_LG: str = "14px"
    SIZE_XL: str = "16px"
    SIZE_2XL: str = "18px"
    SIZE_3XL: str = "20px"
    SIZE_4XL: str = "24px"
    SIZE_5XL: str = "28px"
    SIZE_6XL: str = "32px"
    SIZE_HERO: str = "40px"
    SIZE_MEGA: str = "48px"

    WEIGHT_LIGHT: str = "300"
    WEIGHT_NORMAL: str = "400"
    WEIGHT_MEDIUM: str = "500"
    WEIGHT_SEMIBOLD: str = "600"
    WEIGHT_BOLD: str = "700"
    WEIGHT_EXTRABOLD: str = "800"
    WEIGHT_BLACK: str = "900"

    LETTER_TIGHT: str = "-0.02em"
    LETTER_NORMAL: str = "0em"
    LETTER_WIDE: str = "0.02em"
    LETTER_WIDER: str = "0.05em"

    LINE_HEIGHT_TIGHT: str = "1.25"
    LINE_HEIGHT_NORMAL: str = "1.5"
    LINE_HEIGHT_RELAXED: str = "1.75"


@dataclass(frozen=True)
class Shadows:
    """Layered shadow system with warm glow effects."""
    # Standard shadows (neutral dark)
    XS: str = "0 1px 2px rgba(0,0,0,0.4)"
    SM: str = "0 2px 8px rgba(0,0,0,0.45)"
    MD: str = "0 4px 16px rgba(0,0,0,0.5)"
    LG: str = "0 8px 32px rgba(0,0,0,0.55)"
    XL: str = "0 16px 48px rgba(0,0,0,0.6)"
    XXL: str = "0 24px 64px rgba(0,0,0,0.7)"

    # Glow effects (warm, luxurious)
    ROSE_GLOW: str = "0 0 20px rgba(201,149,107,0.15)"
    ROSE_GLOW_STRONG: str = "0 0 30px rgba(201,149,107,0.25)"
    ROSE_GLOW_INTENSE: str = "0 0 40px rgba(201,149,107,0.35)"

    AMBER_GLOW: str = "0 0 20px rgba(212,168,83,0.15)"
    AMBER_GLOW_STRONG: str = "0 0 30px rgba(212,168,83,0.25)"

    TEAL_GLOW: str = "0 0 20px rgba(61,184,156,0.15)"
    ERROR_GLOW: str = "0 0 20px rgba(224,85,85,0.15)"

    # Elevated shadow (for cards, dialogs)
    ELEVATED: str = "0 8px 32px rgba(0,0,0,0.5), 0 0 1px rgba(201,149,107,0.1)"
    ELEVATED_HOVER: str = "0 12px 40px rgba(0,0,0,0.6), 0 0 1px rgba(201,149,107,0.2)"

    # Inset shadow (for inputs, wells)
    INSET: str = "inset 0 2px 4px rgba(0,0,0,0.3)"
    INSET_FOCUS: str = "inset 0 2px 4px rgba(0,0,0,0.2), 0 0 0 1px rgba(201,149,107,0.5)"


@dataclass(frozen=True)
class Transitions:
    """Easing functions for smooth, premium interactions."""
    INSTANT: str = "80ms ease"
    FAST: str = "120ms ease"
    NORMAL: str = "200ms ease"
    SMOOTH: str = "300ms cubic-bezier(0.4, 0, 0.2, 1)"
    SLOW: str = "400ms cubic-bezier(0.4, 0, 0.2, 1)"
    DRAMATIC: str = "500ms cubic-bezier(0.34, 1.56, 0.64, 1)"
    SPRING: str = "600ms cubic-bezier(0.175, 0.885, 0.32, 1.1)"
    GLACIAL: str = "800ms cubic-bezier(0.4, 0, 0.2, 1)"


@dataclass(frozen=True)
class ZIndex:
    """Layer ordering for overlapping elements."""
    DROPDOWN: int = 100
    STICKY: int = 200
    FIXED: int = 300
    TOOLTIP: int = 400
    POPOVER: int = 500
    MODAL_BACKDROP: int = 600
    MODAL: int = 700
    NOTIFICATION: int = 800
    TOAST: int = 900


# ── Singleton Instances ─────────────────────────────────────────────
C = Colors()
S = Spacing()
R = Radius()
T = Typography()
SH = Shadows()
TR = Transitions()
Z = ZIndex()


def qss(selector: str, **props) -> str:
    """
    Generate QSS block with token values.
    Usage: qss('QPushButton', background=C.BG_TERTIARY, border=f"1px solid {C.BORDER_DEFAULT}")
    """
    import re
    def to_kebab(s):
        return re.sub(r'_([a-z])', lambda m: '-' + m.group(1), s)

    lines = [f"{selector} {{"]
    for k, v in props.items():
        if v is not None:
            lines.append(f"  {to_kebab(k)}: {v};")
    lines.append("}")
    return "\n".join(lines)