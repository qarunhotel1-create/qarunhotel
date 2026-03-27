#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إصلاح مشكلة رفع الملفات في نظام العملاء
"""

import requests
import json
import base64
import os
from datetime import datetime

def test_file_upload():
    """اختبار رفع الملفات"""
    
    # إعدادات الاختبار
    base_url = "http://127.0.0.1:5000"
    customer_id = 1  # معرف العميل للاختبار
    
    print("=" * 50)
    print("اختبار إصلاح مشكلة رفع الملفات")
    print("=" * 50)
    
    # إنشاء ملف اختبار
    test_content = f"""
    هذا ملف اختبار لنظام رفع الوثائق
    تم إنشاؤه في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    محتوى الاختبار:
    - النص العربي يعمل بشكل صحيح ✓
    - الأرقام: 1234567890
    - الرموز: !@#$%^&*()
    
    هذا الملف يهدف لاختبار:
    1. رفع الملفات النصية
    2. معالجة النصوص العربية
    3. حفظ الملفات في النظام
    4. عرض الملفات في واجهة المستخدم
    """
    
    # تحويل المحتوى إلى base64
    content_bytes = test_content.encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')
    data_url = f"data:text/plain;charset=utf-8;base64,{content_base64}"
    
    # بيانات الوثيقة
    document_data = {
        "id": int(datetime.now().timestamp() * 1000),
        "name": "ملف_اختبار_رفع_الوثائق.txt",
        "size": len(content_bytes),
        "type": "text/plain",
        "data": data_url,
        "method": "upload"
    }
    
    # بيانات الطلب
    form_data = {
        'customer_id': str(customer_id),
        'new_documents_data': json.dumps([document_data])
    }
    
    print(f"1. اختبار API للتحقق من البيانات...")
    try:
        # اختبار API التحقق أولاً
        response = requests.post(
            f"{base_url}/customers-new/api/test-upload",
            data=form_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ نجح الاختبار: {result.get('message', 'غير محدد')}")
            print(f"   - عدد الوثائق: {result.get('documents_count', 0)}")
            print(f"   - مفاتيح النموذج: {result.get('form_keys', [])}")
        else:
            print(f"   ✗ فشل الاختبار: {response.status_code}")
            print(f"   - الاستجابة: {response.text}")
            
    except Exception as e:
        print(f"   ✗ خطأ في الاختبار: {str(e)}")
    
    print(f"\n2. اختبار رفع الملف الفعلي...")
    try:
        # محاولة رفع الملف عبر النموذج
        response = requests.post(
            f"{base_url}/customers-new/{customer_id}/edit",
            data=form_data,
            timeout=60,
            allow_redirects=False
        )
        
        if response.status_code in [200, 302]:
            print(f"   ✓ نجح رفع الملف: {response.status_code}")
            if response.status_code == 302:
                print(f"   - تم التوجيه إلى: {response.headers.get('Location', 'غير محدد')}")
        else:
            print(f"   ✗ فشل رفع الملف: {response.status_code}")
            print(f"   - الاستجابة: {response.text[:500]}...")
            
    except Exception as e:
        print(f"   ✗ خطأ في رفع الملف: {str(e)}")
    
    print(f"\n3. معلومات الملف المرفوع:")
    print(f"   - الاسم: {document_data['name']}")
    print(f"   - الحجم: {document_data['size']} بايت")
    print(f"   - النوع: {document_data['type']}")
    print(f"   - الطريقة: {document_data['method']}")
    
    print(f"\n4. نصائح لحل المشاكل:")
    print(f"   - تأكد من تشغيل الخادم على {base_url}")
    print(f"   - تأكد من وجود العميل رقم {customer_id}")
    print(f"   - تأكد من تسجيل الدخول والصلاحيات")
    print(f"   - راجع سجلات الخادم للأخطاء")
    
    print("=" * 50)
    print("انتهى الاختبار")
    print("=" * 50)

if __name__ == "__main__":
    test_file_upload()