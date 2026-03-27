#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لإضافة عمود user_id إلى جدول payments
"""

from hotel import create_app, db
from sqlalchemy import text

def add_user_column_to_payments():
    """إضافة عمود user_id إلى جدول payments"""
    app = create_app()
    
    with app.app_context():
        print("🔧 بدء إضافة عمود user_id إلى جدول payments...")
        
        try:
            # التحقق من وجود العمود
            result = db.engine.execute(text("PRAGMA table_info(payments)"))
            columns = [row[1] for row in result]
            
            if 'user_id' not in columns:
                print("📝 إضافة عمود user_id...")
                db.engine.execute(text("ALTER TABLE payments ADD COLUMN user_id INTEGER"))
                
                # إضافة foreign key constraint (اختياري في SQLite)
                print("🔗 تحديث العلاقات...")
                
                print("✅ تم إضافة عمود user_id بنجاح!")
            else:
                print("ℹ️ عمود user_id موجود بالفعل")
            
            # تحديث الدفعات الموجودة لتشير إلى المستخدم admin
            print("🔄 تحديث الدفعات الموجودة...")
            
            # البحث عن المستخدم admin
            admin_user_result = db.engine.execute(text("SELECT id FROM users WHERE username = 'admin' LIMIT 1"))
            admin_user_row = admin_user_result.fetchone()
            
            if admin_user_row:
                admin_user_id = admin_user_row[0]
                
                # تحديث الدفعات التي لا تحتوي على user_id
                update_result = db.engine.execute(text(
                    "UPDATE payments SET user_id = :admin_id WHERE user_id IS NULL"
                ), admin_id=admin_user_id)
                
                print(f"✅ تم تحديث {update_result.rowcount} دفعة لتشير إلى المستخدم admin")
            else:
                print("⚠️ لم يتم العثور على المستخدم admin")
            
            print("✅ تم إكمال العملية بنجاح!")
            
        except Exception as e:
            print(f"❌ حدث خطأ: {e}")
            return False
        
        return True

if __name__ == '__main__':
    success = add_user_column_to_payments()
    if success:
        print("\n🎉 تم تحديث قاعدة البيانات بنجاح!")
        print("الآن يمكن تتبع من أضاف كل دفعة")
    else:
        print("\n💥 فشل في تحديث قاعدة البيانات")
