import glob
import os
import re

directory = r"c:\Users\aboun\Desktop\Logical Version trae\src\ui\dialogs"
files = glob.glob(os.path.join(directory, "*.py"))

for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # 1. Add import
    if "from src.ui.widgets.base_dialog import BaseDialog" not in content:
        content = content.replace(
            "from PySide6.QtWidgets import",
            "from src.ui.widgets.base_dialog import BaseDialog\nfrom PySide6.QtWidgets import",
            1,
        )

    # 2. Change base class
    content = re.sub(r"class (\w+)\(QDialog\):", r"class \1(BaseDialog):", content)

    # 3. Remove translucent background and frameless window hint (BaseDialog handles it)
    content = re.sub(r"\s*#?\s*self\.setAttribute\(Qt\.WA_TranslucentBackground\)\s*", "\n", content)
    content = re.sub(
        r"\s*self\.setWindowFlags\(Qt\.FramelessWindowHint \| Qt\.Dialog\)\s*",
        "\n",
        content,
    )

    # 4. Remove all the duplicate frame, shadow, and titlebar code
    pattern_to_remove = re.compile(
        r"\s*#?\s*تخطيط جذري شفاف\s*root_layout\s*=\s*QVBoxLayout\(self\).*?(?:layout\s*=\s*content_layout|layout\s*=\s*QVBoxLayout\(content_widget\))",  # noqa: E501
        re.DOTALL,
    )

    match = pattern_to_remove.search(content)
    if match:
        content = content[: match.start()] + "\n        layout = self.content_layout\n" + content[match.end() :]
    else:
        pattern_to_remove_alt = re.compile(
            r"\s*#?\s*تخطيط جذري شفاف\s*root_layout\s*=\s*QVBoxLayout\(self\).*?layout\.addWidget\(self\.title_bar\)",
            re.DOTALL,
        )
        match_alt = pattern_to_remove_alt.search(content)
        if match_alt:
            content = (
                content[: match_alt.start()] + "\n        layout = self.content_layout\n" + content[match_alt.end() :]
            )
        else:
            pattern_to_remove_alt2 = re.compile(
                r"\s*root_layout\s*=\s*QVBoxLayout\(self\).*?layout\.addWidget\(self\.title_bar\)",
                re.DOTALL,
            )
            match_alt2 = pattern_to_remove_alt2.search(content)
            if match_alt2:
                content = (
                    content[: match_alt2.start()]
                    + "\n        layout = self.content_layout\n"
                    + content[match_alt2.end() :]
                )

    # Remove QGraphicsDropShadowEffect, CustomTitleBar imports if they exist to clean up
    content = re.sub(r"from src\.ui\.widgets\.custom_title_bar import CustomTitleBar\s*", "", content)

    # Check if there is self.setWindowTitle or self.i18n.get_message("xxx_title")
    title_match = re.search(
        r"self\.title_bar\s*=\s*CustomTitleBar\(self,\s*title=([^,]+),",
        original_content,
    )
    dialog_title = '""'
    if title_match:
        dialog_title = title_match.group(1).strip()

    # Change `super().__init__(parent)` to `super().__init__(title=..., parent=parent)`
    content = re.sub(
        r"super\(\)\.__init__\(parent\)",
        f"super().__init__(title={dialog_title}, parent=parent)",
        content,
    )

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        # print(f"Refactored: {os.path.basename(filepath)}")
