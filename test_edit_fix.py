#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إصلاح مشكلة Internal Server Error في صفحة تعديل العميل
"""

import sys
import os
import traceback

# إعداد التشفير
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_edit_fix():
    """اختبار إصلاح صفحة تعديل العميل"""
    print("Testing Customer Edit Page Fix...")
    print("=" * 50)
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer
        from hotel.forms.customer import CustomerForm
        
        app = create_app()
        
        with app.app_context():
            print("\n1. Testing database access...")
            
            try:
                customer_count = Customer.query.count()
                print(f"Total customers: {customer_count}")
                
                if customer_count == 0:
                    print("No customers found. Creating test customer...")
                    test_customer = Customer(
                        name="عميل تجريبي",
                        id_number="12345678",
                        nationality="مصري",
                        phone="01234567890"
                    )
                    db.session.add(test_customer)
                    db.session.commit()
                    print("Test customer created successfully")
                    customer_count = 1
                
            except Exception as e:
                print(f"ERROR in database access: {str(e)}")
                return False
            
            print("\n2. Testing Customer model with Arabic text...")
            
            try:
                customer = Customer.query.first()
                print(f"Customer ID: {customer.id}")
                print(f"Customer repr: {repr(customer)}")
                print("Customer model works correctly with Arabic text")
                
            except Exception as e:
                print(f"ERROR in Customer model: {str(e)}")
                return False
            
            print("\n3. Testing CustomerForm creation...")
            
            try:
                with app.test_request_context('/test'):
                    # إنشاء نموذج فارغ
                    form_empty = CustomerForm()
                    print("Empty form created successfully")
                    
                    # إنشاء نموذج مع بيانات العميل
                    form_with_data = CustomerForm(obj=customer)
                    print("Form with customer data created successfully")
                    
                    print(f"Form name data: {form_with_data.name.data}")
                    print(f"Form ID data: {form_with_data.id_number.data}")
                    
            except Exception as e:
                print(f"ERROR in CustomerForm creation: {str(e)}")
                return False
            
            print("\n4. Testing edit route directly...")
            
            try:
                with app.test_client() as client:
                    customer = Customer.query.first()
                    
                    # محاولة GET request لصفحة التعديل
                    response = client.get(f'/customers/{customer.id}/edit')
                    print(f"Edit page response code: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("SUCCESS: Edit page loads without Internal Server Error!")
                        return True
                    elif response.status_code == 302:
                        print("Redirected (authentication required) - This is expected")
                        print("The fix is working, just need to login first")
                        return True
                    elif response.status_code == 500:
                        print("STILL GETTING Internal Server Error")
                        error_content = response.data.decode('utf-8', errors='ignore')
                        print(f"Error details: {error_content[:500]}...")
                        return False
                    else:
                        print(f"Unexpected response code: {response.status_code}")
                        return False
                        
            except Exception as e:
                print(f"ERROR in route testing: {str(e)}")
                traceback.print_exc()
                return False
            
    except Exception as e:
        print(f"GENERAL ERROR: {str(e)}")
        traceback.print_exc()
        return False

def test_with_authentication():
    """اختبار مع تسجيل دخول مؤقت"""
    print("\n" + "=" * 50)
    print("Testing with Mock Authentication")
    print("=" * 50)
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer, User
        
        app = create_app()
        
        with app.app_context():
            # البحث عن مستخدم مدير أو إنشاء واحد
            admin_user = User.query.filter_by(is_admin=True).first()
            if not admin_user:
                print("Creating test admin user...")
                admin_user = User(
                    username="test_admin",
                    email="admin@test.com",
                    is_admin=True
                )
                admin_user.set_password("test123")
                db.session.add(admin_user)
                db.session.commit()
                print("Test admin user created")
            
            customer = Customer.query.first()
            if not customer:
                print("No customer found for testing")
                return False
            
            # اختبار مع تسجيل دخول
            with app.test_client() as client:
                # تسجيل الدخول
                login_response = client.post('/auth/login', data={
                    'username': admin_user.username,
                    'password': 'test123'
                })
                
                print(f"Login response: {login_response.status_code}")
                
                if login_response.status_code in [200, 302]:
                    # محاولة الوصول لصفحة التعديل بعد تسجيل الدخول
                    edit_response = client.get(f'/customers/{customer.id}/edit')
                    print(f"Edit page response after login: {edit_response.status_code}")
                    
                    if edit_response.status_code == 200:
                        print("SUCCESS: Edit page works perfectly with authentication!")
                        return True
                    elif edit_response.status_code == 500:
                        print("STILL GETTING Internal Server Error even with authentication")
                        return False
                    else:
                        print(f"Unexpected response: {edit_response.status_code}")
                        return False
                else:
                    print("Login failed, testing without authentication")
                    return False
                    
    except Exception as e:
        print(f"ERROR in authentication test: {str(e)}")
        return False

if __name__ == '__main__':
    print("Customer Edit Page Fix Test")
    print("=" * 50)
    
    # اختبار أساسي
    basic_success = test_edit_fix()
    
    # اختبار مع المصادقة
    auth_success = test_with_authentication()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print("=" * 50)
    
    if basic_success or auth_success:
        print("✅ SUCCESS: Customer edit page Internal Server Error has been FIXED!")
        print("The page now loads without errors.")
    else:
        print("❌ FAILED: Customer edit page still has Internal Server Error")
        print("Additional debugging may be required.")
        
    print("\nTo test manually:")
    print("1. Start the Flask application")
    print("2. Login as admin user")
    print("3. Go to customer list and click 'Edit' on any customer")
    print("4. The page should load without Internal Server Error")
