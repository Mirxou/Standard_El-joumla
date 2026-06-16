#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
عنصر نصي قابل للسحب والتحجيم في محرر القوالب.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem


class DraggableTextItem(QGraphicsTextItem):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def mouseDoubleClickEvent(self, event):
        """Enable text editing on double-click."""
        if self.textInteractionFlags() == Qt.NoTextInteraction:
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        """Disable text editing when focus is lost."""
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        super().focusOutEvent(event)

    def itemChange(self, change, value):
        """Ensure the item stays within the scene boundaries."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            scene_rect = self.scene().sceneRect()
            item_rect = self.boundingRect()

            # Keep item within horizontal boundaries
            if new_pos.x() < scene_rect.left():
                new_pos.setX(scene_rect.left())
            elif new_pos.x() + item_rect.width() > scene_rect.right():
                new_pos.setX(scene_rect.right() - item_rect.width())

            # Keep item within vertical boundaries
            if new_pos.y() < scene_rect.top():
                new_pos.setY(scene_rect.top())
            elif new_pos.y() + item_rect.height() > scene_rect.bottom():
                new_pos.setY(scene_rect.bottom() - item_rect.height())

            return new_pos
        return super().itemChange(change, value)
