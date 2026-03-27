#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
إصلاح مشكلة UNIQUE constraint failed: customers.id_number
"""

import sqlite3
import os
import sys
import traceback
from datetime import datetime
import uuid

# إعداد التشفير للنظام
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    # للتوافق مع إصدارات Python القديمة
    pass
os.environ['PYTHONIOENCODING'] = 'utf-8'

# مسار قاعدة البيانات
db_path = 'instance/hotel.db'

def check_database():
    """التحقق من وجود قاعدة البيانات"""
    print("التحقق من وجود قاعدة البيانات...")
    if not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة في المسار: {db_path}")
        return None
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"✓ تم الاتصال بقاعدة البيانات بنجاح: {db_path}")
        return conn, cursor
    except sqlite3.Error as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

def check_empty_id_numbers(conn, cursor):
    """التحقق من وجود أرقام هوية فارغة متكررة"""
    print("\nالتحقق من وجود أرقام هوية فارغة متكررة...")
    try:
        cursor.execute("SELECT id, name, id_number FROM customers WHERE id_number = '' OR id_number IS NULL;")
        empty_ids = cursor.fetchall()
        
        if empty_ids:
            print(f"⚠️ تم العثور على {len(empty_ids)} عميل بدون رقم هوية:")
            for customer in empty_ids:
                print(f"  - العميل ID={customer[0]}, الاسم={customer[1]}, رقم الهوية={customer[2]}")
        else:
            print("✓ لا يوجد عملاء بدون رقم هوية")
            
        return empty_ids
    except sqlite3.Error as e:
        print(f"❌ خطأ في التحقق من أرقام الهوية الفارغة: {e}")
        return None

def fix_database_schema(conn, cursor):
    
    print("\nإصلاح هيكل قاعدة البيانات...")
    try:
        # تعطيل قيود المفاتيح الخارجية مؤقتًا
        cursor.execute("PRAGMA foreign_keys=OFF;")
        print("✓ تم تعطيل قيود المفاتيح الخارجية مؤقتًا")
        
        # التحقق من وجود الجدول customers_new وحذفه إذا كان موجودًا
        cursor.execute("DROP TABLE IF EXISTS customers_new;")
        
        # الحصول على معلومات عن جدول customers
        cursor.execute("PRAGMA table_info(customers);")
        columns_info = cursor.fetchall()
        print(f"✓ تم الحصول على معلومات الجدول: {len(columns_info)} عمود")
        
        # إنشاء جدول جديد مع نفس الهيكل ولكن مع تغيير حقل id_number ليكون قابل للقيم الفارغة
        create_table_sql = "CREATE TABLE customers_new (\n"
        for col in columns_info:
            col_id, col_name, col_type, col_notnull, col_default, col_pk = col
            
            # تعديل حقل id_number ليكون قابل للقيم الفارغة
            if col_name == 'id_number':
                create_table_sql += f"    {col_name} {col_type} UNIQUE,\n"
                print(f"✓ تم تعديل حقل {col_name} ليكون فريدًا ولكن يقبل القيم الفارغة")
            else:
                # الحفاظ على باقي الأعمدة كما هي
                not_null = "NOT NULL" if col_notnull else ""
                default = f"DEFAULT {col_default}" if col_default is not None else ""
                primary_key = "PRIMARY KEY" if col_pk else ""
                
                create_table_sql += f"    {col_name} {col_type} {primary_key} {default} {not_null},\n"
        
        # إزالة الفاصلة الأخيرة وإغلاق قوس الجدول
        create_table_sql = create_table_sql.rstrip(",\n") + "\n);"
        
        # إنشاء الجدول الجديد
        cursor.execute(create_table_sql)
        print("✓ تم إنشاء الجدول الجديد بنجاح")
        
        # نقل البيانات من الجدول القديم إلى الجدول الجديد
        cursor.execute("INSERT INTO customers_new SELECT * FROM customers;")
        print("✓ تم نقل البيانات إلى الجدول الجديد")
        
        # حذف الجدول القديم
        cursor.execute("DROP TABLE customers;")
        print("✓ تم حذف الجدول القديم")
        
        # إعادة تسمية الجدول الجديد
        cursor.execute("ALTER TABLE customers_new RENAME TO customers;")
        print("✓ تم إعادة تسمية الجدول الجديد")
        
        # إعادة تفعيل قيود المفاتيح الخارجية
        cursor.execute("PRAGMA foreign_keys=ON;")
        print("✓ تم إعادة تفعيل قيود المفاتيح الخارجية")
        
        # حفظ التغييرات
        conn.commit()
        print("✓ تم حفظ التغييرات بنجاح")
        
        return True
    except sqlite3.Error as e:
        print(f"❌ خطأ في إصلاح هيكل قاعدة البيانات: {e}")
        conn.rollback()
        return False
    
def verify_database_update(conn, cursor):
    """التحقق من نجاح تحديث قاعدة البيانات"""
    print("\nالتحقق من نجاح تحديث قاعدة البيانات...")
    try:
        # التحقق من نجاح العملية
        cursor.execute("PRAGMA table_info(customers);")
        new_columns_info = cursor.fetchall()
        id_number_nullable = True
        
        for col in new_columns_info:
            if col[1] == 'id_number':
                id_number_nullable = col[3] == 0  # إذا كانت القيمة 0 فهذا يعني أن الحقل قابل للقيم الفارغة
        
        if id_number_nullable:
            print("✅ تم تحديث قاعدة البيانات بنجاح. حقل id_number الآن يقبل القيم الفارغة.")
        else:
            print("⚠️ تم تحديث قاعدة البيانات ولكن حقل id_number لا يزال غير قابل للقيم الفارغة.")
        
        return id_number_nullable
    except sqlite3.Error as e:
        print(f"❌ خطأ في التحقق من تحديث قاعدة البيانات: {e}")
        return False

def fix_empty_id_numbers(conn, cursor):
    """إصلاح أرقام الهوية الفارغة المتكررة"""
    print("\nإصلاح أرقام الهوية الفارغة المتكررة...")
    try:
        # البحث عن العملاء بدون رقم هوية
        cursor.execute("SELECT id, name FROM customers WHERE id_number = '' OR id_number IS NULL;")
        customers_without_id = cursor.fetchall()
        
        if not customers_without_id:
            print("✓ لا يوجد عملاء بدون رقم هوية")
            return True
        
        print(f"تم العثور على {len(customers_without_id)} عميل بدون رقم هوية")
        
        # تحديث أرقام الهوية الفارغة بقيم فريدة
        updated_count = 0
        for customer_id, customer_name in customers_without_id:
            try:
                # إنشاء رقم هوية مؤقت فريد
                temp_id = f"TEMP-{uuid.uuid4().hex[:8]}-{customer_id}"
                
                # تحديث رقم الهوية
                cursor.execute("UPDATE customers SET id_number = ? WHERE id = ?", (temp_id, customer_id))
                updated_count += 1
                
                print(f"  - تم تحديث العميل {customer_id}: {customer_name} برقم هوية مؤقت: {temp_id}")
                
            except Exception as e:
                print(f"خطأ في تحديث العميل {customer_id}: {str(e)}")
                continue
        
        # حفظ التغييرات
        conn.commit()
        print(f"✓ تم تحديث {updated_count} عميل بأرقام هوية مؤقتة فريدة")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ خطأ في إصلاح أرقام الهوية الفارغة: {e}")
        conn.rollback()
        return False

def show_form_modification_instructions():
    """عرض تعليمات تعديل نموذج العميل"""
    print("\nتعليمات لتعديل نموذج العميل للتعامل مع أرقام الهوية الفارغة:")
    print("="*50)
    
    print("\n1. تعديل ملف hotel/forms/customer.py:")
    print("""
    def validate_id_number(self, id_number):
        # Skip validation if no data is provided
        if not id_number.data or not id_number.data.strip():
            return
            
        # Clean the ID number by removing any whitespace
        clean_id = id_number.data.strip()
        
        # Check if ID number already exists for another customer
        query = Customer.query.filter(Customer.id_number == clean_id)
        
        # If this is an update (customer_id exists), exclude the current customer from the check
        if hasattr(self, 'customer_id') and self.customer_id is not None:
            query = query.filter(Customer.id != self.customer_id)
        
        # If we find any matching customer (other than the current one), raise validation error
        if query.first() is not None:
            raise ValidationError('رقم الهوية مستخدم بالفعل، الرجاء التحقق من الرقم')
    """)
    
    print("\n2. تعديل ملف hotel/routes/customer.py:")
    print("""
    # في دالة create و edit
    customer = Customer(
        name=form.name.data,
        id_number=form.id_number.data.strip() if form.id_number.data else None,  # استخدام None بدلاً من سلسلة فارغة
        phone=form.phone.data,
        nationality=form.nationality.data,
        marital_status=form.marital_status.data,
        address=form.address.data
    )
    """)
    
    return True

def main():
    """الدالة الرئيسية"""
    print("إصلاح مشكلة UNIQUE constraint failed: customers.id_number")
    print("="*50)
    
    # التحقق من وجود قاعدة البيانات
    db_connection = check_database()
    if not db_connection:
        print("❌ فشل في الاتصال بقاعدة البيانات")
        return False
    
    conn, cursor = db_connection
    
    try:
        # التحقق من وجود أرقام هوية فارغة
        empty_ids = check_empty_id_numbers(conn, cursor)
        
        # إصلاح هيكل قاعدة البيانات
        if not fix_database_schema(conn, cursor):
            print("❌ فشل في إصلاح هيكل قاعدة البيانات")
            return False
        
        # التحقق من نجاح التحديث
        if not verify_database_update(conn, cursor):
            print("❌ فشل في التحقق من تحديث قاعدة البيانات")
            return False
        
        # إصلاح أرقام الهوية الفارغة
        if not fix_empty_id_numbers(conn, cursor):
            print("❌ فشل في إصلاح أرقام الهوية الفارغة")
            return False
        
        # عرض تعليمات تعديل نموذج العميل
        show_form_modification_instructions()
        
        print("\n✅ تم إصلاح مشكلة UNIQUE constraint failed: customers.id_number بنجاح!")
        print("يمكنك الآن إضافة عملاء بدون رقم هوية بدون مشاكل.")
        return True
        
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # إغلاق الاتصال بقاعدة البيانات
        if conn:
            conn.close()
            print("تم إغلاق الاتصال بقاعدة البيانات")

if __name__ == '__main__':
    success = main()