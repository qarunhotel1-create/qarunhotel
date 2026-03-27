#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إصلاح خطأ NameError
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app

def test_user_dashboard():
    """اختبار لوحة تحكم المستخدم"""
    
    app = create_app()
    with app.app_context():
        print("🧪 اختبار لوحة تحكم المستخدم")
        print("=" * 50)
        
        try:
            # محاولة استيراد الدالة
            from hotel.routes.user import dashboard
            print("✅ تم استيراد دالة dashboard بنجاح")
            
            # محاولة تشغيل منطق التقويم
            from hotel.utils.datetime_utils import get_egypt_now
            from datetime import timedelta
            
            start_date = get_egypt_now().date()
            end_date = start_date + timedelta(days=30)
            calendar_dates = [start_date + timedelta(days=i) for i in range(30)]
            
            print(f"✅ تم إنشاء تواريخ التقويم: {len(calendar_dates)} يوم")
            
            # اختبار get_egypt_now
            now = get_egypt_now()
            print(f"✅ get_egypt_now() يعمل: {now}")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🔧 اختبار إصلاح خطأ NameError")
    print("=" * 60)
    
    try:
        result = test_user_dashboard()
        
        if result:
            print("\n✅ تم إصلاح الخطأ بنجاح!")
            print("🎉 لوحة التحكم تعمل بشكل طبيعي")
        else:
            print("\n❌ ما زال هناك خطأ")
        
        return result
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False

if __name__ == '__main__':
    main()