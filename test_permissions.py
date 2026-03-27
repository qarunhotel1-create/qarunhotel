#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لاختبار نظام الصلاحيات وإنشاء مستخدم تجريبي
"""

from hotel import create_app, db
from hotel.models import Permission, User

def test_permissions():
    """اختبار نظام الصلاحيات"""
    app = create_app()
    
    with app.app_context():
        print("🧪 اختبار نظام الصلاحيات...")
        
        # عرض جميع الصلاحيات
        permissions = Permission.query.all()
        print(f"\n📋 الصلاحيات المتاحة ({len(permissions)}):")
        for perm in permissions:
            print(f"   • {perm.name}: {perm.description}")
        
        # عرض المستخدمين وصلاحياتهم
        users = User.query.all()
        print(f"\n👥 المستخدمون ({len(users)}):")
        for user in users:
            print(f"\n🔹 {user.username} ({user.full_name}):")
            print(f"   الصلاحيات: {[p.name for p in user.permissions]}")
            
            # اختبار بعض الصلاحيات المهمة
            test_perms = [
                ('manage_payments', user.can_add_payment()),
                ('manage_bookings', user.can_create_booking()),
                ('check_in_out', user.can_check_in_out()),
                ('admin', user.has_permission('admin'))
            ]
            
            print("   اختبار الصلاحيات:")
            for perm_name, has_perm in test_perms:
                status = "✅" if has_perm else "❌"
                print(f"     {status} {perm_name}")
        
        # إنشاء مستخدم تجريبي مع صلاحيات كاملة
        test_user = User.query.filter_by(username='test_user').first()
        if not test_user:
            print("\n🆕 إنشاء مستخدم تجريبي...")
            
            # الحصول على صلاحيات مهمة
            important_perms = Permission.query.filter(
                Permission.name.in_([
                    'manage_bookings', 'manage_payments', 'manage_customers',
                    'create_booking', 'edit_booking', 'check_in_out',
                    'add_payment', 'edit_payment', 'view_reports'
                ])
            ).all()
            
            test_user = User(
                username='test_user',
                password='test123',
                full_name='مستخدم تجريبي',
                permissions=important_perms
            )
            
            db.session.add(test_user)
            db.session.commit()
            
            print(f"✅ تم إنشاء المستخدم التجريبي: test_user / test123")
            print(f"   الصلاحيات المعطاة: {[p.name for p in important_perms]}")
        else:
            print(f"\n👤 المستخدم التجريبي موجود: {test_user.username}")
        
        # اختبار نهائي للمستخدم التجريبي
        print(f"\n🔍 اختبار المستخدم التجريبي:")
        test_functions = [
            ('إضافة دفعة', test_user.can_add_payment()),
            ('إنشاء حجز', test_user.can_create_booking()),
            ('تعديل حجز', test_user.can_edit_booking()),
            ('تسجيل دخول/خروج', test_user.can_check_in_out()),
            ('عرض التقارير', test_user.can_view_reports()),
            ('إدارة العملاء', test_user.can_manage_customers()),
        ]
        
        for func_name, can_do in test_functions:
            status = "✅" if can_do else "❌"
            print(f"   {status} {func_name}")
        
        print("\n✅ انتهى اختبار الصلاحيات!")
        print("\n📝 معلومات تسجيل الدخول:")
        print("   👑 Admin: admin / admin")
        print("   👤 Test User: test_user / test123")

if __name__ == '__main__':
    test_permissions()
