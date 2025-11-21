"""
خدمة الملاحظات على الفواتير
Invoice Notes Service

إدارة الملاحظات المرتبطة بالفواتير (ملاحظات داخلية / تظهر للعميل)
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.core.database_manager import DatabaseManager
from src.core.database_manager import DatabaseManager as DB

logger = logging.getLogger(__name__)

class NotesService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_note(
        self,
        sale_id: int,
        note_text: str,
        created_by: Optional[int] = None,
        is_internal: bool = False,
        is_pinned: bool = False
    ) -> Dict[str, Any]:
        try:
            self.db.execute_query(
                """
                INSERT INTO invoice_notes (sale_id, note_text, created_by, is_internal, is_pinned)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sale_id, note_text, created_by, 1 if is_internal else 0, 1 if is_pinned else 0)
            )
            note_id = self.db.get_last_insert_id()
            return {"success": True, "id": note_id}
        except Exception as e:
            logger.error(f"Failed to add note: {e}")
            return {"success": False, "error": str(e)}

    def list_notes(self, sale_id: int, include_internal: bool = True) -> List[Dict[str, Any]]:
        try:
            if include_internal:
                rows = self.db.execute_query(
                    "SELECT * FROM invoice_notes WHERE sale_id = ? ORDER BY is_pinned DESC, created_at DESC",
                    (sale_id,)
                )
            else:
                rows = self.db.execute_query(
                    "SELECT * FROM invoice_notes WHERE sale_id = ? AND is_internal = 0 ORDER BY is_pinned DESC, created_at DESC",
                    (sale_id,)
                )
            return rows
        except Exception as e:
            logger.error(f"Failed to list notes: {e}")
            return []

    def pin_note(self, note_id: int, pinned: bool = True) -> bool:
        try:
            self.db.execute_query(
                "UPDATE invoice_notes SET is_pinned = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (1 if pinned else 0, note_id)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to pin note: {e}")
            return False

    def delete_note(self, note_id: int) -> bool:
        try:
            self.db.execute_query("DELETE FROM invoice_notes WHERE id = ?", (note_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete note: {e}")
            return False

# Helper accessors
_notes_service_global: Optional[NotesService] = None

def init_notes_service(db: DatabaseManager) -> NotesService:
    global _notes_service_global
    _notes_service_global = NotesService(db)
    return _notes_service_global

def get_notes_service() -> Optional[NotesService]:
    return _notes_service_global
