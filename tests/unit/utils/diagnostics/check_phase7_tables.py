#!/usr/bin/env python3
import sqlite3


def check_phase7_tables():
    conn = sqlite3.connect("data/erp_system.db")
    cursor = conn.cursor()

    # استعلام للعثور على جداول المرحلة 7
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND (name LIKE '%ai_%'
             OR name LIKE '%decision_%'
             OR name LIKE '%forecast_%'
             OR name LIKE '%business_%'
             OR name LIKE '%customer_segment%')
    """)

    tables = cursor.fetchall()
    # print('✅ جداول المرحلة 7 المُنشأة:')
    for table in tables:
        # print(f'  - {table[0]}')
        pass

    if not tables:
        # print('❌ لم يتم العثور على جداول المرحلة 7')
        pass

    conn.close()


if __name__ == "__main__":
    check_phase7_tables()
