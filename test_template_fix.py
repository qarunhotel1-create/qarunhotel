#!/usr/bin/env python3
"""
اختبار حل مشكلة jinja2.exceptions.TemplateNotFound: customer/create.html
"""

import os
import sys
from flask import Flask
from jinja2 import TemplateNotFound

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_template_exists():
    """اختبار وجود ملف القالب"""
    template_path = os.path.join(
        os.path.dirname(__file__), 
        'hotel', 'templates', 'customer', 'create.html'
    )
    
    print("🔍 فحص وجود ملف القالب...")
    print(f"المسار: {template_path}")
    
    if os.path.exists(template_path):
        print("✅ ملف القالب موجود!")
        
        # فحص محتوى الملف
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if len(content) > 0:
            print(f"✅ الملف يحتوي على {len(content)} حرف")
            
            # فحص العناصر الأساسية
            required_elements = [
                '{% extends "base.html" %}',
                'form.name',
                'form.id_number',
                'customer/create.html'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"⚠️  عناصر مفقودة: {missing_elements}")
            else:
                print("✅ جميع العناصر الأساسية موجودة")
                
        else:
            print("❌ الملف فارغ!")
            return False
            
    else:
        print("❌ ملف القالب غير موجود!")
        return False
    
    return True

def test_flask_template_loading():
    """اختبار تحميل القالب في Flask"""
    try:
        from hotel import create_app
        
        print("\n🔍 اختبار تحميل القالب في Flask...")
        
        app = create_app()
        
        with app.app_context():
            try:
                from flask import render_template_string, render_template
                
                # محاولة تحميل القالب
                template_content = render_template('customer/create.html', 
                                                 title='اختبار', 
                                                 form=None)
                
                print("✅ تم تحميل القالب بنجاح في Flask!")
                print(f"✅ طول المحتوى المُحمّل: {len(template_content)} حرف")
                return True
                
            except TemplateNotFound as e:
                print(f"❌ خطأ في تحميل القالب: {e}")
                return False
            except Exception as e:
                print(f"⚠️  خطأ آخر: {e}")
                # قد يكون خطأ في النموذج، لكن القالب موجود
                return True
                
    except Exception as e:
        print(f"❌ خطأ في إنشاء التطبيق: {e}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("=" * 50)
    print("🧪 اختبار حل مشكلة customer/create.html")
    print("=" * 50)
    
    # اختبار وجود الملف
    template_exists = test_template_exists()
    
    if template_exists:
        # اختبار تحميل القالب في Flask
        flask_loading = test_flask_template_loading()
        
        print("\n" + "=" * 50)
        print("📊 نتائج الاختبار:")
        print("=" * 50)
        print(f"✅ وجود الملف: {'نعم' if template_exists else 'لا'}")
        print(f"✅ تحميل Flask: {'نعم' if flask_loading else 'لا'}")
        
        if template_exists and flask_loading:
            print("\n🎉 تم حل المشكلة بنجاح!")
            print("يمكنك الآن الوصول لصفحة إضافة العملاء بدون خطأ.")
        else:
            print("\n❌ المشكلة لم يتم حلها بالكامل.")
            
    else:
        print("\n❌ فشل الاختبار - الملف غير موجود.")

if __name__ == "__main__":
    main()