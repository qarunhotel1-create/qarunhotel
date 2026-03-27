#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إضافة عمود notes إلى جدول customers إذا لم يكن موجودًا.
مناسب لـ SQLite ضمن instance/hotel.db.
"""
import os
import sqlite3

DB_RELATIVE = os.path.join('instance', 'hotel.db')

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def main():
    db_path = DB_RELATIVE
    if not os.path.exists(db_path):
        print(f"❌ لم يتم العثور على قاعدة البيانات: {db_path}")
        return

    print(f"🔧 تحديث قاعدة البيانات: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        if not column_exists(cur, 'customers', 'notes'):
            print("➡️ إضافة عمود notes إلى customers...")
            cur.execute("ALTER TABLE customers ADD COLUMN notes TEXT")
            conn.commit()
            print("✅ تم إضافة العمود notes بنجاح.")
        else:
            print("✅ عمود notes موجود بالفعل.")
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("تم الانتهاء.")

if __name__ == '__main__':
    main()