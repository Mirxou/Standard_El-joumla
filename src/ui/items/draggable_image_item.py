#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
عنصر صورة قابل للسحب والتحجيم في محرر القوالب.
"""

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem


class DraggableImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(pixmap, parent)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.image_path = None  # To store the path of the image for saving

    def set_image_path(self, path: str):
        self.image_path = path

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
