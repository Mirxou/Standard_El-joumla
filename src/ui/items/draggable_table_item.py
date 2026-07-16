#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
عنصر جدول قابل للسحب والتحجيم في محرر القوالب.
Uses a QGraphicsProxyWidget to embed a QTableWidget in the scene.
"""

from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsProxyWidget,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class DraggableTableItem(QGraphicsProxyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create the widget to be embedded
        self.table = QTableWidget(4, 4)  # 4x4 table as default
        self.table.setHorizontalHeaderLabels(["المنتج", "الكمية", "السعر", "الإجمالي"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setMinimumSectionSize(120)
        self.table.horizontalHeader().setDefaultSectionSize(150)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Example items
        self.table.setItem(0, 0, QTableWidgetItem("منتج تجريبي 1"))
        self.table.setItem(0, 1, QTableWidgetItem("1"))
        self.table.setItem(0, 2, QTableWidgetItem("150.00"))
        self.table.setItem(0, 3, QTableWidgetItem("150.00"))

        # Set the widget for the proxy
        self.setWidget(self.table)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        """Ensure the item stays within the scene boundaries."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            scene_rect = self.scene().sceneRect()
            item_rect = self.boundingRect()

            if new_pos.x() < scene_rect.left():
                new_pos.setX(scene_rect.left())
            elif new_pos.x() + item_rect.width() > scene_rect.right():
                new_pos.setX(scene_rect.right() - item_rect.width())

            if new_pos.y() < scene_rect.top():
                new_pos.setY(scene_rect.top())
            elif new_pos.y() + item_rect.height() > scene_rect.bottom():
                new_pos.setY(scene_rect.bottom() - item_rect.height())

            return new_pos
        return super().itemChange(change, value)

    def get_structure(self):
        """Returns a serializable dictionary of the table's structure."""
        return {
            "column_count": self.table.columnCount(),
            "headers": [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())],
        }
