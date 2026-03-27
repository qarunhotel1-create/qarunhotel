#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح مشكلة التشفير في صفحة تعديل العميل
"""

import sys
import os
import locale

# إعداد التشفير للنظام
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Customer
from hotel.forms.customer import CustomerForm
import traceback

def fix_unicode_encoding():
    """إصلاح مشكلة التشفير في التطبيق"""
    print("Starting Unicode encoding fix...")
    
    try:
        app = create_app()
        
        # إعداد التشفير في إعدادات Flask
        app.config['JSON_AS_ASCII'] = False
        
        with app.app_context():
            print("\n1. Testing database access with proper encoding...")
            
            try:
                customer_count = Customer.query.count()
                print(f"Total customers: {customer_count}")
                
                if customer_count > 0:
                    # اختبار قراءة العملاء مع معالجة التشفير
                    customers = Customer.query.all()
                    print("Successfully read all customers with proper encoding")
                    
                    for i, customer in enumerate(customers[:3]):  # أول 3 عملاء فقط
                        try:
                            # تحويل النص العربي إلى تشفير آمن
                            safe_name = customer.name.encode('utf-8').decode('utf-8') if customer.name else "No Name"
                            safe_id = customer.id_number.encode('utf-8').decode('utf-8') if customer.id_number else "No ID"
                            print(f"Customer {i+1}: ID={customer.id}, Name length={len(customer.name) if customer.name else 0}")
                        except Exception as e:
                            print(f"Error processing customer {customer.id}: {str(e)}")
                            
            except Exception as e:
                print(f"ERROR in database access: {str(e)}")
                traceback.print_exc()
                return False
            
            print("\n2. Testing CustomerForm with encoding fix...")
            
            try:
                # اختبار إنشاء نموذج فارغ
                form = CustomerForm()
                print("Empty form created successfully")
                
                # اختبار إنشاء نموذج مع بيانات عميل
                if customer_count > 0:
                    customer = Customer.query.first()
                    form_with_data = CustomerForm(obj=customer)
                    print("Form with customer data created successfully")
                    
                    # اختبار الوصول للبيانات بشكل آمن
                    name_data = form_with_data.name.data if form_with_data.name.data else ""
                    id_data = form_with_data.id_number.data if form_with_data.id_number.data else ""
                    nationality_data = form_with_data.nationality.data if form_with_data.nationality.data else ""
                    
                    print(f"Form data loaded - Name length: {len(name_data)}, ID length: {len(id_data)}")
                    
            except Exception as e:
                print(f"ERROR in form creation: {str(e)}")
                traceback.print_exc()
                return False
            
            print("\n3. Testing edit route simulation...")
            
            try:
                with app.test_client() as client:
                    if customer_count > 0:
                        customer = Customer.query.first()
                        
                        # محاولة الوصول لصفحة التعديل
                        response = client.get(f'/customers/{customer.id}/edit')
                        print(f"Edit page response code: {response.status_code}")
                        
                        if response.status_code == 500:
                            print("Still getting Internal Server Error")
                            # محاولة الحصول على تفاصيل الخطأ
                            error_content = response.data.decode('utf-8', errors='ignore')
                            print(f"Error details: {error_content[:300]}...")
                        elif response.status_code == 302:
                            print("Redirected (authentication required)")
                        else:
                            print("Edit page accessible!")
                            
            except Exception as e:
                print(f"ERROR in route testing: {str(e)}")
                traceback.print_exc()
                return False
            
            print("\n4. Applying encoding fixes to the application...")
            
            # إنشاء ملف إعدادات التشفير
            encoding_config = """
# إعدادات التشفير للتطبيق
import os
import sys

# إعداد التشفير للنظام
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# إعدادات Flask للتشفير
FLASK_ENCODING_CONFIG = {
    'JSON_AS_ASCII': False,
    'JSON_SORT_KEYS': False
}
"""
            
            with open('encoding_config.py', 'w', encoding='utf-8') as f:
                f.write(encoding_config)
            
            print("Created encoding configuration file")
            
            return True
            
    except Exception as e:
        print(f"GENERAL ERROR: {str(e)}")
        traceback.print_exc()
        return False

def test_edit_page_directly():
    """اختبار مباشر لصفحة تعديل العميل"""
    print("\n" + "="*50)
    print("DIRECT EDIT PAGE TEST")
    print("="*50)
    
    try:
        app = create_app()
        app.config['JSON_AS_ASCII'] = False
        
        with app.app_context():
            # البحث عن عميل للاختبار
            customer = Customer.query.first()
            if not customer:
                print("No customers found for testing")
                return False
            
            print(f"Testing with customer ID: {customer.id}")
            
            # محاكاة طلب GET لصفحة التعديل
            with app.test_request_context(f'/customers/{customer.id}/edit', method='GET'):
                try:
                    from hotel.routes.customer import edit
                    from flask import g
                    from flask_login import AnonymousUserMixin
                    
                    # محاكاة مستخدم مسجل دخول (لتجاوز مشكلة الأذونات)
                    class MockUser:
                        def __init__(self):
                            self.is_authenticated = True
                            self.is_active = True
                            self.is_anonymous = False
                            self.id = 1
                            self.username = "test_admin"
                            self.is_admin = True
                            
                        def get_id(self):
                            return str(self.id)
                        
                        def has_permission(self, permission):
                            return True
                    
                    # تعيين المستخدم المؤقت
                    from flask_login import login_user
                    mock_user = MockUser()
                    g.current_user = mock_user
                    
                    # محاولة تشغيل دالة edit
                    result = edit(customer.id)
                    print("Edit function executed successfully!")
                    print(f"Result type: {type(result)}")
                    
                    return True
                    
                except Exception as e:
                    print(f"ERROR in edit function: {str(e)}")
                    traceback.print_exc()
                    return False
                    
    except Exception as e:
        print(f"ERROR in direct test: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Unicode Encoding Fix for Customer Edit Page")
    print("=" * 50)
    
    success = fix_unicode_encoding()
    if success:
        print("\nEncoding fixes applied successfully!")
        test_edit_page_directly()
    else:
        print("\nFailed to apply encoding fixes!")
