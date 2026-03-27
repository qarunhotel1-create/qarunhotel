#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشخيص عميق لمشكلة Internal Server Error في صفحة تعديل العميل
"""

import sys
import os
import traceback
import logging
from io import StringIO

# إعداد التشفير
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def capture_real_error():
    """محاولة التقاط الخطأ الحقيقي من التطبيق"""
    print("Deep Diagnosis: Capturing Real Error from Edit Page")
    print("=" * 60)
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer
        
        app = create_app()
        
        with app.app_context():
            # البحث عن عميل للاختبار
            customer = Customer.query.first()
            if not customer:
                print("No customers found. Creating test customer...")
                customer = Customer(
                    name="عميل تجريبي للاختبار",
                    id_number="TEST123456",
                    nationality="مصري"
                )
                db.session.add(customer)
                db.session.commit()
                print(f"Created test customer with ID: {customer.id}")
            
            print(f"Testing with customer: ID={customer.id}, Name={customer.name}")
            
            # إعداد logging لالتقاط الأخطاء
            log_capture = StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setLevel(logging.ERROR)
            app.logger.addHandler(handler)
            app.logger.setLevel(logging.DEBUG)
            
            # محاولة محاكاة الطلب الفعلي
            with app.test_client() as client:
                try:
                    print("\n1. Testing GET request to edit page...")
                    response = client.get(f'/customers/{customer.id}/edit', 
                                        follow_redirects=False)
                    
                    print(f"Response Status: {response.status_code}")
                    print(f"Response Headers: {dict(response.headers)}")
                    
                    if response.status_code == 500:
                        print("\n*** INTERNAL SERVER ERROR CONFIRMED ***")
                        
                        # محاولة الحصول على تفاصيل الخطأ
                        error_content = response.data.decode('utf-8', errors='ignore')
                        print(f"Error Response Content (first 1000 chars):")
                        print("-" * 50)
                        print(error_content[:1000])
                        print("-" * 50)
                        
                        # فحص سجل الأخطاء
                        log_contents = log_capture.getvalue()
                        if log_contents:
                            print(f"\nCaptured Log Errors:")
                            print("-" * 50)
                            print(log_contents)
                            print("-" * 50)
                        
                        return True, error_content, log_contents
                        
                    elif response.status_code == 302:
                        print("Redirected - probably to login page")
                        location = response.headers.get('Location', 'Unknown')
                        print(f"Redirect Location: {location}")
                        return False, f"Redirect to: {location}", ""
                        
                    elif response.status_code == 200:
                        print("Page loaded successfully!")
                        return False, "Success", ""
                        
                    else:
                        print(f"Unexpected status code: {response.status_code}")
                        return False, f"Status: {response.status_code}", ""
                        
                except Exception as request_error:
                    print(f"ERROR during request: {str(request_error)}")
                    traceback.print_exc()
                    return True, str(request_error), traceback.format_exc()
                    
    except Exception as e:
        print(f"GENERAL ERROR: {str(e)}")
        traceback.print_exc()
        return True, str(e), traceback.format_exc()

def test_direct_route_execution():
    """اختبار تشغيل route مباشرة لالتقاط الخطأ"""
    print("\n" + "=" * 60)
    print("Direct Route Execution Test")
    print("=" * 60)
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer
        from hotel.routes.customer import edit
        from flask import g
        
        app = create_app()
        
        with app.app_context():
            customer = Customer.query.first()
            if not customer:
                print("No customer for testing")
                return False, "No customer", ""
            
            print(f"Testing direct execution of edit({customer.id})")
            
            # محاولة تشغيل الدالة مباشرة
            with app.test_request_context(f'/customers/{customer.id}/edit', method='GET'):
                try:
                    # محاكاة مستخدم مسجل دخول
                    class MockUser:
                        def __init__(self):
                            self.is_authenticated = True
                            self.is_active = True
                            self.is_anonymous = False
                            self.id = 1
                            self.is_admin = True
                            
                        def get_id(self):
                            return str(self.id)
                        
                        def has_permission(self, permission):
                            return True
                    
                    g.current_user = MockUser()
                    
                    # تشغيل دالة edit
                    result = edit(customer.id)
                    print("SUCCESS: edit() function executed without error!")
                    print(f"Result type: {type(result)}")
                    
                    return False, "Success", ""
                    
                except Exception as edit_error:
                    print(f"ERROR in edit() function: {str(edit_error)}")
                    error_trace = traceback.format_exc()
                    print("Full traceback:")
                    print("-" * 50)
                    print(error_trace)
                    print("-" * 50)
                    
                    return True, str(edit_error), error_trace
                    
    except Exception as e:
        print(f"ERROR in direct test: {str(e)}")
        return True, str(e), traceback.format_exc()

def test_form_creation_isolated():
    """اختبار إنشاء النموذج بشكل منفصل"""
    print("\n" + "=" * 60)
    print("Isolated Form Creation Test")
    print("=" * 60)
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer
        from hotel.forms.customer import CustomerForm
        
        app = create_app()
        
        with app.app_context():
            customer = Customer.query.first()
            if not customer:
                print("No customer for testing")
                return False, "No customer", ""
            
            print(f"Testing CustomerForm creation with customer {customer.id}")
            
            # اختبار إنشاء النموذج في سياق طلب
            with app.test_request_context('/test'):
                try:
                    form = CustomerForm(obj=customer)
                    print("SUCCESS: CustomerForm created successfully!")
                    print(f"Form name data: {form.name.data}")
                    print(f"Form ID data: {form.id_number.data}")
                    
                    return False, "Success", ""
                    
                except Exception as form_error:
                    print(f"ERROR creating CustomerForm: {str(form_error)}")
                    error_trace = traceback.format_exc()
                    print("Full traceback:")
                    print("-" * 50)
                    print(error_trace)
                    print("-" * 50)
                    
                    return True, str(form_error), error_trace
                    
    except Exception as e:
        print(f"ERROR in form test: {str(e)}")
        return True, str(e), traceback.format_exc()

def test_template_rendering():
    """اختبار عرض template"""
    print("\n" + "=" * 60)
    print("Template Rendering Test")
    print("=" * 60)
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer
        from hotel.forms.customer import CustomerForm
        from flask import render_template
        
        app = create_app()
        
        with app.app_context():
            customer = Customer.query.first()
            if not customer:
                print("No customer for testing")
                return False, "No customer", ""
            
            print(f"Testing template rendering for customer {customer.id}")
            
            with app.test_request_context('/test'):
                try:
                    form = CustomerForm(obj=customer)
                    
                    # محاولة عرض template
                    rendered = render_template('customer/edit.html',
                                             title=f'تعديل العميل - {customer.name}',
                                             form=form,
                                             customer=customer)
                    
                    print("SUCCESS: Template rendered successfully!")
                    print(f"Rendered content length: {len(rendered)}")
                    
                    return False, "Success", ""
                    
                except Exception as template_error:
                    print(f"ERROR rendering template: {str(template_error)}")
                    error_trace = traceback.format_exc()
                    print("Full traceback:")
                    print("-" * 50)
                    print(error_trace)
                    print("-" * 50)
                    
                    return True, str(template_error), error_trace
                    
    except Exception as e:
        print(f"ERROR in template test: {str(e)}")
        return True, str(e), traceback.format_exc()

if __name__ == '__main__':
    print("DEEP DIAGNOSIS: Customer Edit Page Internal Server Error")
    print("=" * 70)
    
    # تشغيل جميع الاختبارات
    tests = [
        ("Real Error Capture", capture_real_error),
        ("Direct Route Execution", test_direct_route_execution),
        ("Form Creation", test_form_creation_isolated),
        ("Template Rendering", test_template_rendering)
    ]
    
    errors_found = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            has_error, error_msg, error_trace = test_func()
            if has_error:
                errors_found.append({
                    'test': test_name,
                    'error': error_msg,
                    'trace': error_trace
                })
                print(f"❌ {test_name}: FAILED")
            else:
                print(f"✅ {test_name}: PASSED")
        except Exception as e:
            errors_found.append({
                'test': test_name,
                'error': str(e),
                'trace': traceback.format_exc()
            })
            print(f"❌ {test_name}: CRASHED - {str(e)}")
    
    # تلخيص النتائج
    print("\n" + "=" * 70)
    print("DIAGNOSIS SUMMARY")
    print("=" * 70)
    
    if errors_found:
        print(f"❌ Found {len(errors_found)} error(s):")
        for i, error in enumerate(errors_found, 1):
            print(f"\n{i}. {error['test']}:")
            print(f"   Error: {error['error']}")
            if error['trace']:
                print(f"   Trace: {error['trace'][:200]}...")
    else:
        print("✅ All tests passed - the issue might be environment-specific")
        
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    if errors_found:
        print("1. Review the specific errors above")
        print("2. Apply targeted fixes based on the error details")
        print("3. Re-test after each fix")
    else:
        print("1. Test manually in the actual application")
        print("2. Check server logs during manual testing")
        print("3. Verify authentication and permissions")
