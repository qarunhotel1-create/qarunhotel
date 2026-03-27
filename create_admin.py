#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# إضافة المسار الحالي إلى Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    from hotel import create_app, db
    from hotel.models.user import User, ROLE_ADMIN
    
    print("إنشاء التطبيق...")
    app = create_app()
    
    with app.app_context():
        print("إنشاء جداول قاعدة البيانات...")
        db.create_all()
        
        print("التحقق من وجود مستخدم الإدارة...")
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print("مستخدم الإدارة موجود بالفعل")
            print(f"اسم المستخدم: {admin.username}")
            print(f"الدور: {admin.role}")
            
            # تحديث كلمة المرور للتأكد
            admin.set_password('admin')
            db.session.commit()
            print("تم تحديث كلمة المرور")
            
        else:
            print("إنشاء مستخدم الإدارة...")
            admin = User(
                username='admin',
                password='admin',
                role=ROLE_ADMIN
            )
            db.session.add(admin)
            db.session.commit()
            print("تم إنشاء مستخدم الإدارة بنجاح")
        
        # التحقق من كلمة المرور
        if admin.check_password('admin'):
            print("✓ كلمة المرور صحيحة")
        else:
            print("✗ كلمة المرور غير صحيحة")
            
        print("\nبيانات تسجيل الدخول:")
        print("اسم المستخدم: admin")
        print("كلمة المرور: admin")
        print("الرابط: http://127.0.0.1:5000")
        
except Exception as e:
    print(f"خطأ: {e}")
    import traceback
    traceback.print_exc()
