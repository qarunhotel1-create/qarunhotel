#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريپت تشخيص خطأ Internal Server Error في صفحة تعديل العميل
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Customer
from hotel.forms.customer import CustomerForm
from flask import Flask
import traceback

def diagnose_edit_error():
    """تشخيص مشكلة صفحة تعديل العميل"""
    print("بدء تشخيص مشكلة صفحة تعديل العميل...")
    
    try:
        # إنشاء التطبيق
        app = create_app()
        
        with app.app_context():
            print("\n1. فحص قاعدة البيانات...")
            
            # فحص وجود جدول العملاء
            try:
                customer_count = Customer.query.count()
                print(f"جدول العملاء موجود - عدد العملاء: {customer_count}")
            except Exception as e:
                print(f"خطأ في جدول العملاء: {str(e)}")
                return False
            
            # فحص أول عميل
            if customer_count > 0:
                try:
                    first_customer = Customer.query.first()
                    print(f"أول عميل: {first_customer.name} (ID: {first_customer.id})")
                    
                    # فحص الحقول المطلوبة
                    required_fields = ['name', 'id_number', 'nationality', 'created_at', 'updated_at']
                    for field in required_fields:
                        if hasattr(first_customer, field):
                            value = getattr(first_customer, field)
                            print(f"   - {field}: {value}")
                        else:
                            print(f"الحقل المفقود: {field}")
                            
                except Exception as e:
                    print(f"خطأ في قراءة بيانات العميل: {str(e)}")
                    traceback.print_exc()
                    return False
            
            print("\n2. فحص نموذج CustomerForm...")
            
            # اختبار إنشاء نموذج فارغ
            try:
                form = CustomerForm()
                print("تم إنشاء نموذج فارغ بنجاح")
            except Exception as e:
                print(f"خطأ في إنشاء نموذج فارغ: {str(e)}")
                traceback.print_exc()
                return False
            
            # اختبار إنشاء نموذج مع عميل موجود
            if customer_count > 0:
                try:
                    customer = Customer.query.first()
                    form_with_data = CustomerForm(obj=customer)
                    print("تم إنشاء نموذج مع بيانات العميل بنجاح")
                    
                    # فحص البيانات المحملة في النموذج
                    print(f"   - الاسم: {form_with_data.name.data}")
                    print(f"   - رقم الهوية: {form_with_data.id_number.data}")
                    print(f"   - الجنسية: {form_with_data.nationality.data}")
                    
                except Exception as e:
                    print(f"خطأ في إنشاء نموذج مع بيانات العميل: {str(e)}")
                    traceback.print_exc()
                    return False
            
            print("\n3. فحص template صفحة التعديل...")
            
            # فحص وجود ملف template
            template_path = os.path.join("hotel", "templates", "customer", "edit.html")
            if os.path.exists(template_path):
                print("ملف template موجود")
            else:
                print(f"ملف template مفقود: {template_path}")
                return False
            
            print("\n4. محاولة محاكاة طلب GET لصفحة التعديل...")
            
            # محاولة محاكاة الطلب
            try:
                with app.test_client() as client:
                    if customer_count > 0:
                        customer = Customer.query.first()
                        # محاولة الوصول لصفحة التعديل بدون تسجيل دخول أولاً
                        response = client.get(f'/customers/{customer.id}/edit')
                        print(f"   - كود الاستجابة: {response.status_code}")
                        
                        if response.status_code == 302:
                            print("   - تم إعادة التوجيه (ربما لصفحة تسجيل الدخول)")
                        elif response.status_code == 500:
                            print("Internal Server Error تم تأكيده")
                            # محاولة الحصول على تفاصيل الخطأ
                            print(f"   - محتوى الاستجابة: {response.data.decode('utf-8')[:200]}...")
                        else:
                            print("الصفحة تعمل بشكل طبيعي")
                    else:
                        print("لا توجد عملاء للاختبار")
                        
            except Exception as e:
                print(f"خطأ في محاكاة الطلب: {str(e)}")
                traceback.print_exc()
                return False
            
            print("\n5. فحص الأذونات والمستخدمين...")
            
            # فحص جدول المستخدمين
            try:
                from hotel.models import User
                user_count = User.query.count()
                print(f"عدد المستخدمين: {user_count}")
                
                if user_count > 0:
                    admin_user = User.query.filter_by(is_admin=True).first()
                    if admin_user:
                        print(f"مستخدم مدير موجود: {admin_user.username}")
                    else:
                        print("لا يوجد مستخدم مدير")
                        
            except Exception as e:
                print(f"خطأ في فحص المستخدمين: {str(e)}")
                # هذا ليس خطأ حرج
            
            print("\nانتهى التشخيص. إذا لم تظهر أخطاء واضحة، المشكلة قد تكون في:")
            print("   1. مشكلة في template edit.html")
            print("   2. مشكلة في الأذونات أو تسجيل الدخول")
            print("   3. مشكلة في إعدادات Flask")
            print("   4. مشكلة في حقول قاعدة البيانات المفقودة")
            
            return True
            
    except Exception as e:
        print(f"خطأ عام في التشخيص: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    diagnose_edit_error()
