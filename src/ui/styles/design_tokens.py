"""
Design Tokens — Standard El-Joumla ERP
╔══════════════════════════════════════════════════════════════════╗
║  AURORA NOIR v4.0 — World-Class Arabic ERP Theme              ║
║  Deep Noir + Emerald Gold + Teal Cyan accents                  ║
║  Designed for financial excellence & visual luxury              ║
║  RTL-first · DZD currency context · Premium dark mode          ║
╚══════════════════════════════════════════════════════════════════╝
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Colors:
    """
    Aurora Noir v4.0 — 6-layer depth system with warm metallic gold accents.
    Sophisticated dark palette with emerald gold for financial prestige.
    """
    # ── Backgrounds (6-layer depth architecture) ──────────────────────
    BG_VOID: str = "#06070B"            # Deepest void — window frame, outer space
    BG_DEEP: str = "#0C0E16"            # Deep — outermost app surface
    BG_PRIMARY: str = "#111520"         # Primary — sidebar, titlebar, main surfaces
    BG_SURFACE: str = "#181D2E"         # Surface — cards, panels, dialogs, content areas
    BG_RAISED: str = "#202640"          # Raised — inputs, raised elements, embedded areas
    BG_ELEVATED: str = "#2A3150"        # Elevated — popovers, dropdowns, tooltips
    BG_HOVER: str = "#323C62"           # Hover — interactive hover states
    BG_ACTIVE: str = "#3C4875"          # Active — pressed/selected states
    BG_OVERLAY: str = "rgba(6,7,11,0.80)"  # Overlay — modal/dialog backdrop
    BG_GLASS: str = "rgba(24,29,46,0.88)"   # Glass — frosted glass effect base

    # ── Borders (4-level hierarchy) ───────────────────────────────────
    BORDER_VOID: str = "#111520"         # Invisible border — structural separation
    BORDER_SUBTLE: str = "#1E2440"       # Subtle — between siblings
    BORDER_DEFAULT: str = "#2A3150"      # Default — standard element borders
    BORDER_MEDIUM: str = "#3A4468"       # Medium — emphasized sections
    BORDER_HOVER: str = "#4E5A88"        # Hover — interactive border response
    BORDER_FOCUS: str = "#C8A54E"        # Focus — emerald gold focus ring
    BORDER_GOLD_GLOW: str = "#E8C96A"   # Gold glow — premium focus

    # ── Text (5-level hierarchy for perfect readability) ──────────────
    TEXT_BRIGHT: str = "#FFFFFF"         # Bright — headlines, key data, CTAs
    TEXT_PRIMARY: str = "#F0F2F5"        # Primary — body text, paragraphs
    TEXT_SECONDARY: str = "#8B92A8"      # Secondary — descriptions, meta text
    TEXT_MUTED: str = "#515874"          # Muted — placeholders, hints, timestamps
    TEXT_GHOST: str = "#2E3550"          # Ghost — disabled text, watermarks
    TEXT_INVERSE: str = "#111520"        # Inverse — text on gold/accent backgrounds

    # ── Brand Accents (Emerald Gold + Teal + Coral + Sky) ─────────────
    ACCENT_GOLD: str = "#C8A54E"         # Emerald Gold — primary accent (financial prestige)
    ACCENT_GOLD_LIGHT: str = "#E8C96A"   # Gold Light — hover states, highlights
    ACCENT_GOLD_DARK: str = "#A88A3E"    # Gold Dark — pressed states
    ACCENT_GOLD_SUBTLE: str = "rgba(200,165,78,0.10)"  # Gold subtle bg
    ACCENT_GOLD_GLOW: str = "rgba(200,165,78,0.25)"    # Gold glow effect
    ACCENT_GOLD_SHIMMER: str = "rgba(200,165,78,0.04)" # Gold shimmer hint

    ACCENT_TEAL: str = "#2DD4BF"         # Teal — success, positive, growth
    ACCENT_TEAL_LIGHT: str = "#5EEADB"   # Teal Light
    ACCENT_TEAL_DARK: str = "#14B8A6"    # Teal Dark
    ACCENT_TEAL_SUBTLE: str = "rgba(45,212,191,0.10)"

    ACCENT_CORAL: str = "#EF6B6B"        # Coral — error, danger, alerts
    ACCENT_CORAL_LIGHT: str = "#F59B9B"  # Coral Light
    ACCENT_CORAL_DARK: str = "#DC4444"   # Coral Dark
    ACCENT_CORAL_SUBTLE: str = "rgba(239,107,107,0.10)"

    ACCENT_AMBER: str = "#F59E0B"        # Amber — warning, caution, attention
    ACCENT_AMBER_LIGHT: str = "#FBBF24"  # Amber Light
    ACCENT_AMBER_DARK: str = "#D97706"   # Amber Dark
    ACCENT_AMBER_SUBTLE: str = "rgba(245,158,11,0.10)"

    ACCENT_SKY: str = "#38BDF8"          # Sky Blue — info, links, secondary actions
    ACCENT_SKY_LIGHT: str = "#7DD3FC"    # Sky Light
    ACCENT_SKY_SUBTLE: str = "rgba(56,189,248,0.10)"

    # ── Semantic Colors ──────────────────────────────────────────────
    SUCCESS: str = "#2DD4BF"
    SUCCESS_BG: str = "rgba(45,212,191,0.10)"
    SUCCESS_BORDER: str = "rgba(45,212,191,0.30)"

    WARNING: str = "#F59E0B"
    WARNING_BG: str = "rgba(245,158,11,0.10)"
    WARNING_BORDER: str = "rgba(245,158,11,0.30)"

    ERROR: str = "#EF6B6B"
    ERROR_BG: str = "rgba(239,107,107,0.10)"
    ERROR_BORDER: str = "rgba(239,107,107,0.30)"

    INFO: str = "#38BDF8"
    INFO_BG: str = "rgba(56,189,248,0.10)"
    INFO_BORDER: str = "rgba(56,189,248,0.30)"

    # ── Gradient Presets ─────────────────────────────────────────────
    GRADIENT_GOLD: str = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #C8A54E,stop:1 #E8C96A)"
    GRADIENT_GOLD_H: str = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #C8A54E,stop:1 #E8C96A)"
    GRADIENT_TEAL: str = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #14B8A6,stop:1 #5EEADB)"
    GRADIENT_CORAL: str = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #DC4444,stop:1 #F59B9B)"
    GRADIENT_DARK: str = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #181D2E,stop:1 #111520)"
    GRADIENT_SURFACE: str = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #202640,stop:0.5 #181D2E,stop:1 #111520)"
    GRADIENT_HERO: str = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #C8A54E,stop:0.25 #D4B65A,stop:0.5 #E8C96A,stop:0.75 #F0D87A,stop:1 #FFF1C1)"
    GRADIENT_SIDEBAR: str = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #111520,stop:0.5 #0C0E16,stop:1 #080A12)"
    GRADIENT_AMBER: str = "qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #D97706,stop:1 #FBBF24)"
    GRADIENT_SKY: str = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0EA5E9,stop:1 #7DD3FC)"


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
    XS: str = "0 1px 2px rgba(0,0,0,0.5)"
    SM: str = "0 2px 8px rgba(0,0,0,0.55)"
    MD: str = "0 4px 16px rgba(0,0,0,0.6)"
    LG: str = "0 8px 32px rgba(0,0,0,0.65)"
    XL: str = "0 16px 48px rgba(0,0,0,0.7)"
    XXL: str = "0 24px 64px rgba(0,0,0,0.8)"

    # Glow effects (warm gold, luxurious)
    GOLD_GLOW: str = "0 0 20px rgba(200,165,78,0.15)"
    GOLD_GLOW_STRONG: str = "0 0 30px rgba(200,165,78,0.25)"
    GOLD_GLOW_INTENSE: str = "0 0 40px rgba(200,165,78,0.35)"

    TEAL_GLOW: str = "0 0 20px rgba(45,212,191,0.15)"
    CORAL_GLOW: str = "0 0 20px rgba(239,107,107,0.15)"
    AMBER_GLOW: str = "0 0 20px rgba(245,158,11,0.15)"
    SKY_GLOW: str = "0 0 20px rgba(56,189,248,0.15)"

    # Elevated shadow (for cards, dialogs)
    ELEVATED: str = "0 8px 32px rgba(0,0,0,0.5), 0 0 1px rgba(200,165,78,0.1)"
    ELEVATED_HOVER: str = "0 12px 40px rgba(0,0,0,0.6), 0 0 1px rgba(200,165,78,0.2)"

    # Inset shadow (for inputs, wells)
    INSET: str = "inset 0 2px 4px rgba(0,0,0,0.3)"
    INSET_FOCUS: str = "inset 0 2px 4px rgba(0,0,0,0.2), 0 0 0 1px rgba(200,165,78,0.5)"


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
    Usage: qss('QPushButton', background=C.BG_RAISED, border=f"1px solid {C.BORDER_DEFAULT}")
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