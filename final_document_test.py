#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import tempfile
from io import BytesIO
sys.path.append('e:/1/QARUN HOTELLL')

from hotel import create_app, db
from hotel.models.customer import Customer
from datetime import datetime

def create_test_file():
    """إنشاء ملف اختبار صغير"""
    content = b"Test document content for customer"
    return BytesIO(content)

def simulate_customer_creation_with_document():
    """محاكاة إضافة عميل جديد مع وثيقة"""
    app = create_app()
    with app.app_context():
        print("=== Final Document Test - Customer Creation Simulation ===")
        
        try:
            # إنشاء العميل
            customer = Customer(
                name="Final Test Customer",
                id_number="FINAL123",
                nationality="Saudi",
                phone="555123456"
            )
            
            db.session.add(customer)
            db.session.flush()
            print(f"✓ Customer created with ID: {customer.id}")
            
            # محاكاة رفع الوثيقة
            filename = f"document_{customer.id}_test.pdf"
            customer.document_filename = filename
            customer.document_type = "id_card"
            customer.document_upload_date = datetime.utcnow()
            
            print(f"✓ Document data assigned:")
            print(f"  - Filename: {customer.document_filename}")
            print(f"  - Type: {customer.document_type}")
            print(f"  - Upload date: {customer.document_upload_date}")
            print(f"  - has_document: {customer.has_document}")
            
            # محاكاة إنشاء الملف الفعلي
            upload_dir = os.path.join(app.static_folder, 'uploads', 'customers')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(b"Test document content")
            
            print(f"✓ Physical file created: {file_path}")
            print(f"  - File exists: {os.path.exists(file_path)}")
            print(f"  - File size: {os.path.getsize(file_path)} bytes")
            
            # حفظ في قاعدة البيانات
            db.session.commit()
            print(f"✓ Customer committed to database")
            
            # التحقق من النتيجة النهائية
            saved_customer = Customer.query.get(customer.id)
            print(f"\n=== Final Verification ===")
            print(f"Customer ID: {saved_customer.id}")
            print(f"Customer name: {saved_customer.name}")
            print(f"Document filename: {saved_customer.document_filename}")
            print(f"Document type: {saved_customer.document_type}")
            print(f"has_document: {saved_customer.has_document}")
            print(f"Document URL: {saved_customer.document_url}")
            print(f"Document type display: {saved_customer.get_document_type_display()}")
            
            # تنظيف الملف التجريبي
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✓ Test file cleaned up")
            
            # حذف العميل التجريبي
            db.session.delete(saved_customer)
            db.session.commit()
            print(f"✓ Test customer removed")
            
            print(f"\n🎉 SUCCESS: Document creation and display should work correctly!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR: {str(e)}")
            return False

def check_current_status():
    """فحص الوضع الحالي"""
    app = create_app()
    with app.app_context():
        print("=== Current System Status ===")
        
        customers = Customer.query.all()
        customers_with_docs = Customer.query.filter(Customer.document_filename.isnot(None)).all()
        
        print(f"Total customers: {len(customers)}")
        print(f"Customers with documents: {len(customers_with_docs)}")
        
        upload_dir = os.path.join(app.static_folder, 'uploads', 'customers')
        files = os.listdir(upload_dir) if os.path.exists(upload_dir) else []
        print(f"Files in upload directory: {len(files)}")
        
        print("\nCustomers with documents:")
        for customer in customers_with_docs:
            try:
                name_safe = customer.name.encode('ascii', 'ignore').decode('ascii')[:20]
            except:
                name_safe = f"Customer_{customer.id}"
            print(f"  - ID: {customer.id}, Name: {name_safe}")
            print(f"    File: {customer.document_filename}")
            print(f"    Type: {customer.document_type}")
            print(f"    has_document: {customer.has_document}")

if __name__ == "__main__":
    check_current_status()
    print("\n" + "="*50)
    simulate_customer_creation_with_document()
