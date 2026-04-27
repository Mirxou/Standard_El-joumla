from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel, 
    QSpacerItem, QSizePolicy, QWidget
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QCursor
from typing import Dict, Optional

class ModernSidebar(QFrame):
    """
    Modern Responsive Sidebar for System 2.0
    Features:
    - Collapsible (Icon-only mode vs Full mode)
    - Animated transitions
    - Glassmorphism styling support
    """
    
    # Signal: page_id, button_text
    page_changed = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modernSidebar")
        
        # Current state
        self.is_collapsed = False
        self.expanded_width = 250
        self.collapsed_width = 70
        
        # Mapping: button_id -> QPushButton
        self.buttons: Dict[str, QPushButton] = {}
        
        self.setup_ui()
        self._apply_styles()
        
    def setup_ui(self):
        """Initialize the UI layout"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 25, 15, 25)
        self.layout.setSpacing(12)
        self.menu_layout = self.layout # Alias for tests
        
        # 1. Header (Logo/Title)
        self._setup_header()
        
        # 2. Toggle Button (Burger Menu)
        self._setup_toggle_btn()
        
        # Spacer
        self.layout.addSpacing(20)
        
        # 3. Navigation Buttons
        self._setup_nav_buttons()
        
        # Checkable logic
        self._current_active_btn = None
        
        # Bottom Spacer
        self.layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding
        ))
        
        # 4. Settings/Logout at bottom
        self._setup_bottom_buttons()

        # Fixed width initially
        self.setFixedWidth(self.expanded_width)
        
    def _apply_styles(self):
        """Apply Glassmorphism and UI/UX Pro Max styles to the sidebar"""
        self.setStyleSheet("""
            QFrame#modernSidebar {
                background-color: rgba(255, 255, 255, 0.85); /* Glass effect */
                border-left: 1px solid rgba(226, 232, 240, 0.9); /* slate-200 */
                border-radius: 0px;
            }
            QLabel#sidebarTitle {
                font-size: 18px;
                font-weight: 800;
                color: #1E293B; /* slate-800 */
                letter-spacing: 1px;
            }
            QPushButton#sidebarToggleBtn {
                background: transparent;
                border: none;
                border-radius: 8px;
                font-size: 20px;
                color: #475569;
                padding: 5px;
            }
            QPushButton#sidebarToggleBtn:hover {
                background-color: #F1F5F9;
                color: #2563EB;
            }
            QPushButton#modernSidebarBtn {
                background: transparent;
                border: none;
                border-radius: 12px;
                text-align: left;
                padding: 12px 16px;
                color: #475569; /* slate-600 */
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton#modernSidebarBtn:hover {
                background-color: rgba(37, 99, 235, 0.08); /* blue-600 with 8% opacity */
                color: #2563EB; /* blue-600 */
            }
            QPushButton#modernSidebarBtn:checked {
                background-color: #2563EB;
                color: white;
            }
            QPushButton#sidebarLogoutBtn {
                color: #EF4444; /* red-500 */
            }
            QPushButton#sidebarLogoutBtn:hover {
                background-color: rgba(239, 68, 68, 0.1);
            }
        """)

    def _setup_header(self):
        """Header with App Title"""
        self.header_container = QFrame()
        self.header_layout = QVBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.app_logo = QLabel("🚀") # Placeholder or Icon
        self.app_logo.setAlignment(Qt.AlignCenter)
        self.app_logo.setStyleSheet("font-size: 24px;")
        
        self.app_title = QLabel("EL-joumLa")
        self.app_title.setObjectName("sidebarTitle")
        self.app_title.setAlignment(Qt.AlignCenter)
        
        self.header_layout.addWidget(self.app_logo)
        self.header_layout.addWidget(self.app_title)
        
        self.layout.addWidget(self.header_container)

    def _setup_toggle_btn(self):
        """Button to toggle collapse state"""
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setObjectName("sidebarToggleBtn")
        self.toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_btn.setToolTip("تبديل القائمة")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        # Add to layout properly (usually at top or separate)
        # For this design, maybe beside title or just below
        # Let's put it at the very top right, effectively acting as menu
        # Removing from here and integrated into header or separate logic if needed.
        # But user wants responsive, so let's keep a distinct toggle.
        self.layout.insertWidget(0, self.toggle_btn, 0, Qt.AlignRight)

    def _setup_nav_buttons(self):
        """Create main navigation items"""
        # Define menu items: (ID, Label, Icon)
        # Note: Icons will need to be set properly. Using text fallback for now if no icon system ready.
        menu_items = [
            ("home", "الرئيسية", "🏠"),
            ("inventory", "المخزون", "📦"),
            ("sales", "المبيعات", "💰"),
            ("purchases", "المشتريات", "🛒"),
            ("payments", "الحسابات", "💳"), # Changed to Al-Hisabat (Accounts)
            ("reports", "التقارير", "📊"),
            ("contacts", "الجهات", "👥"), # Changed to Al-Jahat (Contacts)
            ("performance", "الأداء", "🚀"), # Added Performance
            
            # Application Features
            ("users", "المستخدمين", "👤"),
            ("system", "النظام", "💻"),
            ("audit", "السجلات", "📝"),
            ("notifications", "الإشعارات", "🔔"),
        ]
        
        for btn_id, label, icon_char in menu_items:
            btn = self._create_btn(btn_id, label, icon_char)
            self.layout.addWidget(btn)
            self.buttons[btn_id] = btn

    def _setup_bottom_buttons(self):
        """Bottom actions like Settings"""
        bottom_items = [
            ("settings", "الإعدادات", "⚙️"),
            ("logout", "خروج", "🚪"),
        ]
        
        for btn_id, label, icon_char in bottom_items:
            btn = self._create_btn(btn_id, label, icon_char)
            if btn_id == "logout":
                btn.setObjectName("sidebarLogoutBtn") # Specific styling
            self.layout.addWidget(btn)
            self.buttons[btn_id] = btn

    def _create_btn(self, btn_id: str, label: str, icon_char: str) -> QPushButton:
        """Helper to create a unified sidebar button"""
        btn = QPushButton(f"  {label}")
        btn.setProperty("icon_char", icon_char) # Store for collapsed mode
        btn.setProperty("full_text", label)
        btn.setObjectName("modernSidebarBtn")
        btn.setCheckable(True)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Set icon (using text as placeholder or QIcon if available)
        # Assuming we might swap to QIcon later, but for now text-based icons are reliable
        # We'll use a specific style for text icons
        
        # Connect
        btn.clicked.connect(lambda checked=False, b_id=btn_id, b_text=label: self._on_btn_clicked(b_id, b_text))
        
        return btn

    def _on_btn_clicked(self, btn_id: str, btn_text: str):
        """Handle button selection"""
        # Uncheck all others
        for bid, btn in self.buttons.items():
            if bid != btn_id:
                btn.setChecked(False)
        
        self.buttons[btn_id].setChecked(True)
        self.page_changed.emit(btn_id, btn_text)

    def toggle_sidebar(self):
        """Animate expand/collapse"""
        width_start = self.width()
        width_end = self.collapsed_width if not self.is_collapsed else self.expanded_width
        
        # Animation
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(width_start)
        self.animation.setEndValue(width_end)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)
        
        # Fix maximum width to ensure animation works
        self.setMaximumWidth(width_end) 
        
        self.animation.start()
        
        # Update UI elements
        self.is_collapsed = not self.is_collapsed
        self._update_ui_state()
        
    def _update_ui_state(self):
        """Update labels and icons based on collapsed state"""
        for btn in self.buttons.values():
            icon = btn.property("icon_char")
            label = btn.property("full_text")
            
            if self.is_collapsed:
                btn.setText(icon) # Icon only
                btn.setToolTip(label)
            else:
                btn.setText(f"  {label}") # Restore text
                btn.setToolTip("")
                
        # Header visibility
        if self.is_collapsed:
            self.app_title.hide()
            self.app_logo.show()
        else:
            self.app_title.show()
            self.app_logo.show()

    def set_active(self, page_id: str):
        """Programmatically set active page"""
        if page_id in self.buttons:
            self.buttons[page_id].click()

    # --- Test Suite Compatibility Methods ---
    def add_menu_item(self, label, icon, callback):
        """إضافة عنصر قائمة (توافق مع الاختبارات)"""
        btn_id = label.lower().replace(" ", "_")
        btn = self._create_btn(btn_id, label, icon)
        btn.clicked.connect(callback)
        self.layout.insertWidget(self.layout.count() - 1, btn) # قبل الـ spacer
        self.buttons[btn_id] = btn
        return btn

    def add_separator(self):
        """إضافة فاصل"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #334155; margin: 10px 0;")
        self.layout.insertWidget(self.layout.count() - 1, line)
        return line

    def set_active_item(self, label):
        """تعيين العنصر النشط حسب الاسم"""
        for btn in self.buttons.values():
            if btn.property("full_text") == label:
                btn.click()
                return True
        return False

    def collapse(self):
        """طي الشريط"""
        if not self.is_collapsed:
            self.toggle_sidebar()

    def expand(self):
        """توسيع الشريط"""
        if self.is_collapsed:
            self.toggle_sidebar()

    def toggle(self):
        """تبديل الحالة"""
        self.toggle_sidebar()

    def set_width(self, width):
        """تعيين العرض"""
        self.setFixedWidth(width)

    def get_menu_items(self) -> list:
        """الحصول على عناصر القائمة"""
        return list(self.buttons.values())

    def clear_menu(self):
        """مسح القائمة"""
        for btn in self.buttons.values():
            self.layout.removeWidget(btn)
            btn.deleteLater()
        self.buttons.clear()
