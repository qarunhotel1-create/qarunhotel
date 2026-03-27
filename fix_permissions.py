#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإصلاح نظام الصلاحيات وضمان عمل جميع الميزات
"""

from hotel import create_app, db
from hotel.models import Permission, User

def fix_permissions():
    """إصلاح وتحديث نظام الصلاحيات"""
    app = create_app()
    
    with app.app_context():
        print("🔧 بدء إصلاح نظام الصلاحيات...")
        
        # قائمة الصلاحيات المطلوبة
        required_permissions = [
            {'name': 'admin', 'description': 'إدارة كاملة للنظام'},
            {'name': 'dashboard', 'description': 'الوصول إلى لوحة التحكم'},
            {'name': 'manage_users', 'description': 'إدارة المستخدمين'},
            {'name': 'manage_rooms', 'description': 'إدارة الغرف'},
            {'name': 'manage_bookings', 'description': 'إدارة الحجوزات'},
            {'name': 'manage_customers', 'description': 'إدارة العملاء'},
            {'name': 'manage_payments', 'description': 'إدارة المدفوعات'},
            {'name': 'view_reports', 'description': 'عرض التقارير'},
            {'name': 'delete_data', 'description': 'حذف البيانات'},
            {'name': 'create_booking', 'description': 'إنشاء حجز جديد'},
            {'name': 'edit_booking', 'description': 'تعديل الحجوزات'},
            {'name': 'delete_booking', 'description': 'حذف الحجوزات'},
            {'name': 'check_in_out', 'description': 'تسجيل الدخول والخروج'},
            {'name': 'add_payment', 'description': 'إضافة دفعة جديدة'},
            {'name': 'edit_payment', 'description': 'تعديل الدفعات'},
            {'name': 'delete_payment', 'description': 'حذف الدفعات'},
            {'name': 'transfer_room', 'description': 'نقل الغرف'},
            {'name': 'manage_deus', 'description': 'إدارة حجوزات الديوز'},
        ]
        
        # إضافة الصلاحيات المفقودة
        existing_permissions = {p.name: p for p in Permission.query.all()}
        
        for perm_data in required_permissions:
            if perm_data['name'] not in existing_permissions:
                new_perm = Permission(
                    name=perm_data['name'],
                    description=perm_data['description']
                )
                db.session.add(new_perm)
                print(f"✅ تم إضافة صلاحية: {perm_data['name']} - {perm_data['description']}")
            else:
                # تحديث الوصف إذا كان مختلف
                existing_perm = existing_permissions[perm_data['name']]
                if existing_perm.description != perm_data['description']:
                    existing_perm.description = perm_data['description']
                    print(f"🔄 تم تحديث وصف صلاحية: {perm_data['name']}")
        
        db.session.commit()
        print("💾 تم حفظ الصلاحيات الجديدة")
        
        # التحقق من المستخدمين وصلاحياتهم
        users = User.query.all()
        print(f"\n👥 المستخدمون الموجودون ({len(users)}):")
        
        for user in users:
            print(f"\n🔹 {user.username} ({user.full_name}):")
            print(f"   الصلاحيات: {[p.name for p in user.permissions]}")
            
            # إذا كان المستخدم admin، تأكد من أن لديه صلاحية admin
            if user.username == 'admin':
                admin_perm = Permission.query.filter_by(name='admin').first()
                if admin_perm and admin_perm not in user.permissions:
                    user.permissions.append(admin_perm)
                    print(f"   ✅ تم إضافة صلاحية admin للمستخدم {user.username}")
        
        db.session.commit()
        
        # عرض الصلاحيات النهائية
        print(f"\n📋 جميع الصلاحيات المتاحة ({Permission.query.count()}):")
        for perm in Permission.query.order_by(Permission.name):
            print(f"   • {perm.name}: {perm.description}")
        
        print("\n✅ تم إصلاح نظام الصلاحيات بنجاح!")
        
        # اختبار الصلاحيات
        print("\n🧪 اختبار الصلاحيات:")
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            test_permissions = ['manage_payments', 'manage_bookings', 'manage_users']
            for perm in test_permissions:
                has_perm = admin_user.has_permission(perm)
                status = "✅" if has_perm else "❌"
                print(f"   {status} {perm}: {has_perm}")

if __name__ == '__main__':
    fix_permissions()
