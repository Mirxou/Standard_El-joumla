import pytest
from PySide6.QtWidgets import QPushButton

def test_button_creation(qtbot):
    button = QPushButton("Test")
    qtbot.addWidget(button)
    assert button.text() == "Test"



