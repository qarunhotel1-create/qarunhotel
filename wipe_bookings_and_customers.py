#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت مسح جميع الحجوزات والعملاء (مع البيانات المرتبطة) بشكل آمن
- يحذف بالترتيب الصحيح لتجنب تعارض القيود:
  Payments -> BookingGuests -> RoomTransfers -> Bookings -> CustomerDocuments -> Customers
- يعرض عدد السجلات قبل وبعد
- يطلب تأكيد قبل التنفيذ
"""

import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.payment import Payment
from hotel.models.booking_guest import BookingGuest
from hotel.models.room_transfer import RoomTransfer
from hotel.models.customer import Customer
from hotel.models.document import CustomerDocument


def wipe_bookings_and_customers():
    """حذف جميع الحجوزات والعملاء وجميع البيانات المرتبطة بهم"""
    app = create_app()
    with app.app_context():
        try:
            print("⚠️ تحذير مهم: سيتم حذف جميع الحجوزات والعملاء والبيانات المرتبطة بهم نهائياً!")

            # إحصاءات قبل الحذف
            counts_before = {
                'payments': Payment.query.count(),
                'booking_guests': BookingGuest.query.count(),
                'room_transfers': RoomTransfer.query.count(),
                'bookings': Booking.query.count(),
                'documents': CustomerDocument.query.count(),
                'customers': Customer.query.count(),
            }

            print("\n📊 الإحصاءات قبل الحذف:")
            for k, v in counts_before.items():
                print(f" - {k}: {v}")

            # تنفيذ الحذف بالترتيب الآمن
            deleted = {}

            if counts_before['payments']:
                print("\n🗑️ حذف جميع المدفوعات (payments)...")
                deleted['payments'] = Payment.query.delete(synchronize_session=False)
            else:
                deleted['payments'] = 0

            if counts_before['booking_guests']:
                print("🗑️ حذف جميع المرافقين في الحجوزات (booking_guests)...")
                deleted['booking_guests'] = BookingGuest.query.delete(synchronize_session=False)
            else:
                deleted['booking_guests'] = 0

            if counts_before['room_transfers']:
                print("🗑️ حذف جميع عمليات نقل الغرف (room_transfers)...")
                deleted['room_transfers'] = RoomTransfer.query.delete(synchronize_session=False)
            else:
                deleted['room_transfers'] = 0

            if counts_before['bookings']:
                print("🗑️ حذف جميع الحجوزات (bookings)...")
                deleted['bookings'] = Booking.query.delete(synchronize_session=False)
            else:
                deleted['bookings'] = 0

            if counts_before['documents']:
                print("🗑️ حذف جميع وثائق العملاء (customer_documents)...")
                # حذف الملفات من القرص بشكل اختياري يمكن إضافته لاحقاً
                deleted['documents'] = CustomerDocument.query.delete(synchronize_session=False)
            else:
                deleted['documents'] = 0

            if counts_before['customers']:
                print("🗑️ حذف جميع العملاء (customers)...")
                deleted['customers'] = Customer.query.delete(synchronize_session=False)
            else:
                deleted['customers'] = 0

            # حفظ التغييرات
            db.session.commit()

            print("\n✅ تم الحذف بنجاح. تفاصيل المحذوف:")
            for k, v in deleted.items():
                print(f" - {k}: {v}")

            # التحقق بعد الحذف
            counts_after = {
                'payments': Payment.query.count(),
                'booking_guests': BookingGuest.query.count(),
                'room_transfers': RoomTransfer.query.count(),
                'bookings': Booking.query.count(),
                'documents': CustomerDocument.query.count(),
                'customers': Customer.query.count(),
            }

            print("\n📊 الإحصاءات بعد الحذف:")
            for k, v in counts_after.items():
                print(f" - {k}: {v}")

            if all(v == 0 for v in counts_after.values()):
                print("\n🎉 تم مسح جميع الحجوزات والعملاء بنجاح. يمكنك البدء من جديد.")
            else:
                print("\n⚠️ تحذير: لا تزال هناك سجلات متبقية. راجع الرسائل أعلاه.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ حدث خطأ أثناء الحذف: {e}")
            raise


def main():
    print("⚠️ هذا الإجراء نهائي وغير قابل للتراجع!")
    confirm = input("\nهل أنت متأكد أنك تريد مسح جميع الحجوزات والعملاء؟ اكتب 'نعم' للتأكيد: ")
    if confirm.strip().lower() in ['نعم', 'yes', 'y']:
        wipe_bookings_and_customers()
    else:
        print("❌ تم إلغاء العملية.")


if __name__ == '__main__':
    main()