#!/usr/bin/env python3
"""
خدمة الدعم الفني (Support Ticket & Knowledge Base Service)
تدعم فتح ومتابعة التذاكر والبحث في قاعدة المعرفة
"""

from typing import Any, Dict, List, Optional


class SupportService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self._init_tables()

    def _init_tables(self):
        q1 = """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        q2 = """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute_query(q1)
        self.db.execute_query(q2)

    def create_ticket(self, user_id: int, subject: str, description: str, priority: str = "normal") -> int:
        q = """INSERT INTO support_tickets (user_id, subject, description, priority) VALUES (?, ?, ?, ?)"""
        res = self.db.execute_query(q, (user_id, subject, description, priority))
        return res.lastrowid if hasattr(res, "lastrowid") else None

    def update_ticket_status(self, ticket_id: int, status: str):
        q = """UPDATE support_tickets SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?"""
        self.db.execute_query(q, (status, ticket_id))

    def list_tickets(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if user_id:
            q = "SELECT * FROM support_tickets WHERE user_id=? ORDER BY created_at DESC"
            rows = self.db.fetch_all(q, (user_id,))
        else:
            q = "SELECT * FROM support_tickets ORDER BY created_at DESC"
            rows = self.db.fetch_all(q)
        return [dict(row) for row in rows]

    def add_knowledge(self, question: str, answer: str, tags: Optional[str] = None):
        q = """INSERT INTO knowledge_base (question, answer, tags) VALUES (?, ?, ?)"""
        self.db.execute_query(q, (question, answer, tags))

    def search_knowledge(self, keyword: str) -> List[Dict[str, Any]]:
        q = """SELECT * FROM knowledge_base WHERE question LIKE ? OR answer LIKE ? OR tags LIKE ?"""
        like = f"%{keyword}%"
        rows = self.db.fetch_all(q, (like, like, like))
        return [dict(row) for row in rows]
