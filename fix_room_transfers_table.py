#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح جدول room_transfers لإضافة عمود transfer_time المفقود
"""

import sqlite3
import os
from datetime import datetime

def fix_room_transfers_table():
    """إصلاح جدول room_transfers"""
    
    # مسار قاعدة البيانات
    db_path = 'instance/hotel.db'
    
    if not os.path.exists(db_path):
        print("❌ ملف قاعدة البيانات غير موجود!")
        return False
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 بدء إصلاح جدول room_transfers...")
        
        # التحقق من بنية الجدول الحالية
        cursor.execute("PRAGMA table_info(room_transfers)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"الأعمدة الموجودة حالياً: {columns}")
        
        # التحقق من وجود عمود transfer_time
        if 'transfer_time' not in columns:
            print("⚠️ عمود transfer_time غير موجود، سيتم إضافته...")
            
            # إضافة عمود transfer_time
            cursor.execute("ALTER TABLE room_transfers ADD COLUMN transfer_time DATETIME")
            print("✅ تم إضافة عمود transfer_time")
            
            # تحديث السجلات الموجودة بوقت افتراضي
            cursor.execute("UPDATE room_transfers SET transfer_time = datetime('now') WHERE transfer_time IS NULL")
            print("✅ تم تحديث السجلات الموجودة بوقت افتراضي")
            
        else:
            print("✅ عمود transfer_time موجود بالفعل")
        
        # التحقق من وجود الأعمدة الأخرى المطلوبة
        required_columns = ['transferred_by_user_id', 'reason', 'notes']
        
        for col in required_columns:
            if col not in columns:
                if col == 'transferred_by_user_id':
                    cursor.execute("ALTER TABLE room_transfers ADD COLUMN transferred_by_user_id INTEGER")
                    cursor.execute("UPDATE room_transfers SET transferred_by_user_id = 1 WHERE transferred_by_user_id IS NULL")
                    print(f"✅ تم إضافة عمود {col}")
                elif col in ['reason', 'notes']:
                    cursor.execute(f"ALTER TABLE room_transfers ADD COLUMN {col} TEXT")
                    print(f"✅ تم إضافة عمود {col}")
            else:
                print(f"✅ عمود {col} موجود بالفعل")
        
        # حفظ التغييرات
        conn.commit()
        print("✅ تم حفظ جميع التغييرات")
        
        # التحقق من البنية النهائية
        cursor.execute("PRAGMA table_info(room_transfers)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"البنية النهائية للجدول: {final_columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح الجدول: {e}")
        return False

def verify_table_structure():
    """التحقق من بنية الجدول"""
    db_path = 'instance/hotel.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 التحقق من بنية جدول room_transfers...")
        
        cursor.execute("PRAGMA table_info(room_transfers)")
        columns_info = cursor.fetchall()
        
        print("تفاصيل الأعمدة:")
        for col in columns_info:
            print(f"  - {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # عد السجلات
        cursor.execute("SELECT COUNT(*) FROM room_transfers")
        count = cursor.fetchone()[0]
        print(f"\nعدد السجلات في الجدول: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في التحقق: {e}")
        return False

if __name__ == '__main__':
    print("🏨 إصلاح جدول room_transfers")
    print("=" * 50)
    
    # إصلاح الجدول
    if fix_room_transfers_table():
        print("\n" + "=" * 50)
        print("✅ تم إصلاح الجدول بنجاح!")
        
        # التحقق من النتيجة
        verify_table_structure()
        
        print("\n🎉 يمكنك الآن استخدام ميزة نقل العملاء بدون مشاكل!")
    else:
        print("\n❌ فشل في إصلاح الجدول")
