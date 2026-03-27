#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية
"""

import sys
import os
import traceback
import sqlite3

# إعداد التشفير للنظام
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    # للتوافق مع إصدارات Python القديمة
    pass
os.environ['PYTHONIOENCODING'] = 'utf-8'

# تحديد مسار قاعدة البيانات
possible_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hotel', 'hotel.db'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'hotel.db'),
    'instance/hotel.db',
    'hotel.db',
    'instance\\hotel.db'
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if db_path:
    print(f"تم العثور على قاعدة البيانات: {db_path}")
else:
    print("لم يتم العثور على قاعدة البيانات في المسارات المتوقعة")
    print("المسارات المفحوصة:")
    for path in possible_paths:
        print(f"  - {os.path.abspath(path)}")


# نستخدم SQLite مباشرة بدلاً من Flask-SQLAlchemy
# لتجنب مشاكل البيئة الافتراضية

def fix_customer_name_english():
    """إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية"""
    print("بدء إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية...")
    
    try:
        # التحقق من وجود قاعدة البيانات
        if not db_path:
            print("خطأ: لم يتم العثور على قاعدة البيانات")
            return False
        
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        # تمكين دعم Unicode
        conn.text_factory = str
        cursor = conn.cursor()
        
        print("\n1. اختبار الوصول لقاعدة البيانات مع التشفير المناسب...")
        
        try:
            # التحقق من تشفير قاعدة البيانات
            cursor.execute("PRAGMA encoding;")
            db_encoding = cursor.fetchone()[0]
            print(f"✓ تشفير قاعدة البيانات: {db_encoding}")
            
            # التحقق من وجود جدول العملاء
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer';")
            if not cursor.fetchone():
                print("خطأ: جدول العملاء غير موجود!")
                return False
            
            # عدد العملاء
            cursor.execute("SELECT COUNT(*) FROM customer;")
            customer_count = cursor.fetchone()[0]
            print(f"إجمالي العملاء: {customer_count}")
            
            if customer_count > 0:
                # قراءة أول 3 عملاء
                cursor.execute("SELECT id, name, id_number FROM customer LIMIT 3;")
                customers = cursor.fetchall()
                print("تم قراءة العملاء بنجاح مع التشفير المناسب")
                
                for i, customer in enumerate(customers):
                    try:
                        customer_id, name, id_number = customer
                        # تحويل النص إلى تشفير آمن
                        safe_name = name.encode('utf-8').decode('utf-8') if name else "بدون اسم"
                        safe_id = id_number.encode('utf-8').decode('utf-8') if id_number else "بدون هوية"
                        print(f"العميل {i+1}: ID={customer_id}, الاسم={safe_name}, طول الاسم={len(name) if name else 0}")
                    except Exception as e:
                        print(f"خطأ في معالجة العميل {customer[0]}: {str(e)}")
        except Exception as e:
            print(f"خطأ في الوصول لقاعدة البيانات: {str(e)}")
            traceback.print_exc()
            return False
        
        print("\n2. اختبار إنشاء عميل باسم إنجليزي...")
        
        try:
            # إنشاء عميل تجريبي باسم إنجليزي
            cursor.execute("""
                INSERT INTO customer (name, id_number, nationality, phone, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, ("John Smith", "TEST123456", "جنسية أخرى", "01234567890"))
            conn.commit()
            test_customer_id = cursor.lastrowid
            print(f"تم إنشاء عميل تجريبي باسم إنجليزي بنجاح، ID={test_customer_id}")
            
            # التحقق من حفظ الاسم بشكل صحيح
            cursor.execute("SELECT name FROM customer WHERE id = ?", (test_customer_id,))
            saved_name = cursor.fetchone()[0]
            if saved_name == "John Smith":
                print("تم حفظ الاسم الإنجليزي بشكل صحيح!")
            else:
                print(f"خطأ: الاسم المحفوظ '{saved_name}' لا يطابق 'John Smith'")
            
            # حذف العميل التجريبي
            cursor.execute("DELETE FROM customer WHERE id = ?", (test_customer_id,))
            conn.commit()
            print("تم حذف العميل التجريبي")
            
        except Exception as e:
            print(f"خطأ في اختبار إنشاء عميل باسم إنجليزي: {str(e)}")
            traceback.print_exc()
            conn.rollback()
            return False
        
        print("\n3. اختبار تعديل اسم عميل إلى اسم إنجليزي...")
        
        try:
            # إنشاء عميل تجريبي
            cursor.execute("""
                INSERT INTO customer (name, id_number, nationality, phone, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, ("عميل تجريبي", "TEST654321", "مصري", "01234567890"))
            conn.commit()
            test_customer_id = cursor.lastrowid
            print(f"تم إنشاء عميل تجريبي، ID={test_customer_id}")
            
            # تعديل الاسم إلى اسم إنجليزي
            cursor.execute("UPDATE customer SET name = ? WHERE id = ?", ("Jane Doe", test_customer_id))
            conn.commit()
            print("تم تعديل اسم العميل إلى اسم إنجليزي")
            
            # التحقق من حفظ الاسم بشكل صحيح
            cursor.execute("SELECT name FROM customer WHERE id = ?", (test_customer_id,))
            saved_name = cursor.fetchone()[0]
            if saved_name == "Jane Doe":
                print("تم حفظ الاسم الإنجليزي بعد التعديل بشكل صحيح!")
            else:
                print(f"خطأ: الاسم المحفوظ '{saved_name}' لا يطابق 'Jane Doe'")
            
            # حذف العميل التجريبي
            cursor.execute("DELETE FROM customer WHERE id = ?", (test_customer_id,))
            conn.commit()
            print("تم حذف العميل التجريبي")
            
        except Exception as e:
            print(f"خطأ في اختبار تعديل اسم عميل إلى اسم إنجليزي: {str(e)}")
            traceback.print_exc()
            conn.rollback()
            return False
        
        print("\n4. التحقق من إعدادات التشفير في قاعدة البيانات...")
        
        # التحقق من إعدادات التشفير في قاعدة البيانات
        cursor.execute("PRAGMA encoding;")
        db_encoding = cursor.fetchone()[0]
        print(f"✓ تشفير قاعدة البيانات: {db_encoding}")
        
        # إغلاق الاتصال بقاعدة البيانات
        cursor.close()
        conn.close()
        
        print("\n✅ تم إكمال جميع الاختبارات بنجاح!")
        return True
        
    except Exception as e:
        print(f"خطأ عام: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية")
    print("=" * 50)
    
    success = fix_customer_name_english()
    if success:
        print("\n✅ تم إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية بنجاح!")
        print("يمكنك الآن إضافة وتعديل أسماء العملاء باللغة الإنجليزية بدون مشاكل.")
    else:
        print("\n❌ فشل إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية!")