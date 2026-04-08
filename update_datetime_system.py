#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحديث نظام التاريخ والوقت في قاعدة البيانات
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.utils.datetime_utils import get_egypt_now_naive

def update_datetime_system():
    """تحديث نظام التاريخ والوقت في قاعدة البيانات"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("تحديث نظام التاريخ والوقت في قاعدة البيانات")
        print("=" * 60)
        
        try:
            # إنشاء الجداول إذا لم تكن موجودة
            db.create_all()
            print("✅ تم التأكد من وجود جميع الجداول")
            
            # تحديث الوقت الحالي لجميع السجلات التي لا تحتوي على تاريخ
            from hotel.models.customer import Customer
            from hotel.models.document import CustomerDocument
            from hotel.models.booking import Booking
            from hotel.models.user import User, ActivityLog
            from hotel.models.note import Note
            from hotel.models.booking_guest import BookingGuest
            from hotel.models.room_transfer import RoomTransfer
            
            current_time = get_egypt_now_naive()
            
            # تحديث العملاء
            customers_updated = 0
            for customer in Customer.query.filter(Customer.created_at.is_(None)).all():
                customer.created_at = current_time
                customer.updated_at = current_time
                customers_updated += 1
            
            # تحديث الوثائق
            documents_updated = 0
            for document in CustomerDocument.query.filter(CustomerDocument.created_at.is_(None)).all():
                document.created_at = current_time
                document.updated_at = current_time
                document.upload_date = current_time
                documents_updated += 1
            
            # تحديث المستخدمين
            users_updated = 0
            for user in User.query.filter(User.created_at.is_(None)).all():
                user.created_at = current_time
                users_updated += 1
            
            # تحديث الملاحظات
            notes_updated = 0
            for note in Note.query.filter(Note.created_at.is_(None)).all():
                note.created_at = current_time
                notes_updated += 1
            
            # حفظ التغييرات
            db.session.commit()
            
            print(f"✅ تم تحديث {customers_updated} عميل")
            print(f"✅ تم تحديث {documents_updated} وثيقة")
            print(f"✅ تم تحديث {users_updated} مستخدم")
            print(f"✅ تم تحديث {notes_updated} ملاحظة")
            
            print("\n" + "=" * 60)
            print("تم تحديث نظام التاريخ والوقت بنجاح! ✅")
            print("=" * 60)
            
            # عرض معلومات النظام الجديد
            print(f"\nالوقت الحالي بتوقيت مصر: {current_time}")
            print("النظام الآن يستخدم:")
            print("- توقيت مصر (Africa/Cairo)")
            print("- نظام 12 ساعة مع صباحاً/مساءً")
            print("- تحويل تلقائي من UTC إلى توقيت مصر")
            
        except Exception as e:
            print(f"❌ خطأ في تحديث النظام: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    success = update_datetime_system()
    if success:
        print("\n🎉 تم تحديث النظام بنجاح!")
    else:
        print("\n❌ فشل في تحديث النظام!")
        sys.exit(1)