#!/usr/bin/env python3
"""
ترحيل جدول الوثائق إلى النظام الجديد
يقوم بإنشاء جدول جديد ونقل البيانات الموجودة
"""

import os
import sys
import sqlite3
from datetime import datetime

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_documents_table():
    """ترحيل جدول الوثائق"""
    db_path = os.path.join('instance', 'hotel.db')
    
    if not os.path.exists(db_path):
        print("❌ ملف قاعدة البيانات غير موجود")
        return False
    
    try:
        print("🔄 بدء ترحيل جدول الوثائق...")
        
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # التحقق من وجود الجدول القديم
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_documents'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("📋 جدول الوثائق موجود، سيتم تحديثه...")
            
            # الحصول على بنية الجدول الحالية
            cursor.execute("PRAGMA table_info(customer_documents)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"📊 الأعمدة الحالية: {', '.join(column_names)}")
            
            # إنشاء جدول جديد بالبنية المحدثة
            create_new_table_sql = """
            CREATE TABLE IF NOT EXISTS customer_documents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_name VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_extension VARCHAR(10) NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                document_title VARCHAR(200),
                description TEXT,
                is_scanned BOOLEAN DEFAULT 0,
                scan_method VARCHAR(50) DEFAULT 'upload',
                pages_count INTEGER DEFAULT 1,
                scan_quality VARCHAR(20) DEFAULT 'high',
                scan_resolution INTEGER DEFAULT 300,
                status VARCHAR(20) DEFAULT 'active',
                is_verified BOOLEAN DEFAULT 0,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
            """
            
            cursor.execute(create_new_table_sql)
            print("✅ تم إنشاء الجدول الجديد")
            
            # نقل البيانات الموجودة
            cursor.execute("SELECT * FROM customer_documents")
            old_data = cursor.fetchall()
            
            if old_data:
                print(f"📦 نقل {len(old_data)} سجل...")
                
                for row in old_data:
                    # تحويل البيانات القديمة للتنسيق الجديد
                    old_dict = dict(zip(column_names, row))
                    
                    # إعداد البيانات الجديدة
                    new_data = {
                        'id': old_dict.get('id'),
                        'customer_id': old_dict.get('customer_id'),
                        'filename': old_dict.get('filename', f'doc_{old_dict.get("id", "unknown")}.bin'),
                        'original_name': old_dict.get('original_name', old_dict.get('filename', 'وثيقة غير معروفة')),
                        'file_type': old_dict.get('file_type', 'other'),
                        'file_extension': old_dict.get('file_extension', 'bin'),
                        'file_size': old_dict.get('file_size', 0),
                        'mime_type': old_dict.get('mime_type', 'application/octet-stream'),
                        'document_title': old_dict.get('document_title'),
                        'description': old_dict.get('description'),
                        'is_scanned': old_dict.get('is_scanned', 0),
                        'scan_method': 'scan' if old_dict.get('is_scanned', 0) else 'upload',
                        'pages_count': old_dict.get('scan_pages_count', 1) or 1,
                        'scan_quality': old_dict.get('scan_quality', 'high'),
                        'scan_resolution': old_dict.get('scan_resolution', 300),
                        'status': 'active',
                        'is_verified': old_dict.get('is_verified', 0),
                        'upload_date': old_dict.get('upload_date', old_dict.get('created_at', datetime.now().isoformat())),
                        'created_at': old_dict.get('created_at', datetime.now().isoformat()),
                        'updated_at': old_dict.get('updated_at', datetime.now().isoformat())
                    }
                    
                    # إدراج البيانات في الجدول الجديد
                    insert_sql = """
                    INSERT INTO customer_documents_new 
                    (id, customer_id, filename, original_name, file_type, file_extension, 
                     file_size, mime_type, document_title, description, is_scanned, 
                     scan_method, pages_count, scan_quality, scan_resolution, status, 
                     is_verified, upload_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_sql, (
                        new_data['id'], new_data['customer_id'], new_data['filename'],
                        new_data['original_name'], new_data['file_type'], new_data['file_extension'],
                        new_data['file_size'], new_data['mime_type'], new_data['document_title'],
                        new_data['description'], new_data['is_scanned'], new_data['scan_method'],
                        new_data['pages_count'], new_data['scan_quality'], new_data['scan_resolution'],
                        new_data['status'], new_data['is_verified'], new_data['upload_date'],
                        new_data['created_at'], new_data['updated_at']
                    ))
                
                print("✅ تم نقل جميع البيانات")
            
            # حذف الجدول القديم وإعادة تسمية الجديد
            cursor.execute("DROP TABLE customer_documents")
            cursor.execute("ALTER TABLE customer_documents_new RENAME TO customer_documents")
            
            print("✅ تم استبدال الجدول القديم")
            
        else:
            print("📋 إنشاء جدول الوثائق الجديد...")
            
            # إنشاء جدول جديد
            create_table_sql = """
            CREATE TABLE customer_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_name VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_extension VARCHAR(10) NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                document_title VARCHAR(200),
                description TEXT,
                is_scanned BOOLEAN DEFAULT 0,
                scan_method VARCHAR(50) DEFAULT 'upload',
                pages_count INTEGER DEFAULT 1,
                scan_quality VARCHAR(20) DEFAULT 'high',
                scan_resolution INTEGER DEFAULT 300,
                status VARCHAR(20) DEFAULT 'active',
                is_verified BOOLEAN DEFAULT 0,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
            """
            
            cursor.execute(create_table_sql)
            print("✅ تم إنشاء جدول الوثائق الجديد")
        
        # حفظ التغييرات
        conn.commit()
        
        # التحقق من النتيجة
        cursor.execute("SELECT COUNT(*) FROM customer_documents")
        count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA table_info(customer_documents)")
        new_columns = cursor.fetchall()
        
        print(f"📊 عدد الوثائق في الجدول الجديد: {count}")
        print(f"📋 الأعمدة الجديدة: {len(new_columns)} عمود")
        
        # إغلاق الاتصال
        conn.close()
        
        # إنشاء مجلد الرفع
        upload_folder = os.path.join('hotel', 'static', 'uploads', 'customers')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            print(f"📁 تم إنشاء مجلد الرفع: {upload_folder}")
        
        print("\n" + "="*50)
        print("🎉 تم ترحيل جدول الوثائق بنجاح!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الترحيل: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def test_new_structure():
    """اختبار البنية الجديدة"""
    db_path = os.path.join('instance', 'hotel.db')
    
    try:
        print("\n🧪 اختبار البنية الجديدة...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # اختبار الجدول
        cursor.execute("SELECT COUNT(*) FROM customer_documents")
        count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA table_info(customer_documents)")
        columns = cursor.fetchall()
        
        print(f"✅ الجدول يعمل بشكل صحيح")
        print(f"📊 عدد الوثائق: {count}")
        print(f"📋 عدد الأعمدة: {len(columns)}")
        
        # عرض بعض البيانات التجريبية
        if count > 0:
            cursor.execute("SELECT id, customer_id, original_name, file_type, scan_method, status FROM customer_documents LIMIT 3")
            samples = cursor.fetchall()
            
            print("📄 عينة من الوثائق:")
            for sample in samples:
                print(f"   • ID: {sample[0]}, العميل: {sample[1]}, الاسم: {sample[2]}, النوع: {sample[3]}, الطريقة: {sample[4]}, الحالة: {sample[5]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        return False

if __name__ == '__main__':
    print("🏨 نظام إدارة الفندق - ترحيل جدول الوثائق")
    print("="*50)
    
    if migrate_documents_table():
        if test_new_structure():
            print("\n🚀 النظام جاهز للاستخدام!")
            print("يمكنك الآن تشغيل التطبيق والوصول للنظام الجديد على:")
            print("http://localhost:5000/customers-new/")
        else:
            print("\n⚠️  تم الترحيل ولكن هناك مشاكل في الاختبار")
    else:
        print("\n❌ فشل في ترحيل الجدول")
        sys.exit(1)