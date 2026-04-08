#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from hotel import create_app, db
from hotel.models.room_transfer import RoomTransfer
from datetime import datetime

# اختبار إنشاء سجل نقل
app = create_app()

with app.app_context():
    try:
        print("اختبار إنشاء سجل نقل...")
        
        current_time = datetime.now()
        
        # اختبار إنشاء كائن RoomTransfer
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
            transferred_by_user_id=1,
            reason='اختبار',
            notes='سجل تجريبي'
        )
        
        print("✅ تم إنشاء كائن RoomTransfer بنجاح")
        print(f"نوع الكائن: {type(transfer)}")
        print(f"له _sa_instance_state: {hasattr(transfer, '_sa_instance_state')}")
        
        # اختبار إضافة إلى session
        db.session.add(transfer)
        print("✅ تم إضافة الكائن إلى session بنجاح")
        
        # اختبار commit (لكن سنعمل rollback)
        db.session.commit()
        print("✅ تم commit بنجاح")
        
        # حذف السجل التجريبي
        db.session.delete(transfer)
        db.session.commit()
        print("✅ تم حذف السجل التجريبي")
        
        print("\n🎉 جميع الاختبارات نجحت! النقل يجب أن يعمل الآن.")
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
