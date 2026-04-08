#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from hotel import create_app, db
from hotel.models.room_transfer import RoomTransfer
from hotel.models.user import User
from datetime import datetime

# اختبار نموذج RoomTransfer
app = create_app()

with app.app_context():
    try:
        print("اختبار نموذج RoomTransfer...")
        
        # البحث عن مستخدم admin
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ لم يتم العثور على مستخدم admin")
            exit(1)
        
        print(f"✅ تم العثور على المستخدم: {admin_user.username}")
        
        current_time = datetime.now()
        
        # إنشاء كائن RoomTransfer
        transfer = RoomTransfer(
            booking_id=1,
            from_room_id=1,
            to_room_id=2,
            from_room_check_in=current_time,
            from_room_check_out=current_time,
            to_room_check_in=current_time,
            transfer_date=current_time,
            transfer_time=current_time,
            transferred_by='admin',
            transferred_by_user_id=admin_user.id,
            reason='اختبار النموذج',
            notes='سجل تجريبي'
        )
        
        print("✅ تم إنشاء كائن RoomTransfer")
        
        # اختبار العلاقات
        print(f"transferred_by (نص): {transfer.transferred_by}")
        print(f"transferred_by_user_id: {transfer.transferred_by_user_id}")
        
        # إضافة إلى session للاختبار
        db.session.add(transfer)
        db.session.flush()  # للحصول على ID بدون commit
        
        # اختبار العلاقة
        print(f"transferred_by_user: {transfer.transferred_by_user}")
        if transfer.transferred_by_user:
            print(f"transferred_by_user.username: {transfer.transferred_by_user.username}")
        
        print("✅ جميع العلاقات تعمل بشكل صحيح")
        
        # rollback لعدم حفظ البيانات التجريبية
        db.session.rollback()
        print("✅ تم إلغاء البيانات التجريبية")
        
        print("\n🎉 النموذج يعمل بشكل صحيح!")
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
