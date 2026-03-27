import os
import sys
from datetime import datetime, timedelta
from flask import Flask
from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.payment import Payment
from hotel.utils.datetime_utils import convert_utc_to_egypt, get_egypt_now_naive

# إنشاء تطبيق Flask
app = create_app()

def fix_dates():
    """تصحيح التواريخ في قاعدة البيانات من UTC إلى توقيت مصر"""
    with app.app_context():
        print("بدء تصحيح التواريخ في قاعدة البيانات...")
        
        # تصحيح تواريخ الحجوزات
        bookings = Booking.query.all()
        print(f"تم العثور على {len(bookings)} حجز للتصحيح")
        
        for booking in bookings:
            if booking.created_at:
                try:
                    # تحويل التاريخ من UTC إلى توقيت مصر
                    egypt_time = convert_utc_to_egypt(booking.created_at)
                    # التحقق من نوع الكائن
                    if hasattr(egypt_time, 'hour'):
                        # تحويل التاريخ إلى naive datetime (بدون معلومات المنطقة الزمنية)
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day, 
                                            egypt_time.hour, egypt_time.minute, egypt_time.second)
                    else:
                        # إذا كان الكائن من نوع date فقط
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day)
                    booking.created_at = naive_time
                except Exception as e:
                    print(f"خطأ في تحويل created_at للحجز {booking.id}: {str(e)}")
                    continue
            
            if booking.deus_start_time:
                try:
                    egypt_time = convert_utc_to_egypt(booking.deus_start_time)
                    if hasattr(egypt_time, 'hour'):
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day, 
                                            egypt_time.hour, egypt_time.minute, egypt_time.second)
                    else:
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day)
                    booking.deus_start_time = naive_time
                except Exception as e:
                    print(f"خطأ في تحويل deus_start_time للحجز {booking.id}: {str(e)}")
            
            if booking.deus_end_time:
                try:
                    egypt_time = convert_utc_to_egypt(booking.deus_end_time)
                    if hasattr(egypt_time, 'hour'):
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day, 
                                            egypt_time.hour, egypt_time.minute, egypt_time.second)
                    else:
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day)
                    booking.deus_end_time = naive_time
                except Exception as e:
                    print(f"خطأ في تحويل deus_end_time للحجز {booking.id}: {str(e)}")
        
        # تصحيح تواريخ الدفعات
        payments = Payment.query.all()
        print(f"تم العثور على {len(payments)} دفعة للتصحيح")
        
        for payment in payments:
            if payment.payment_date:
                try:
                    egypt_time = convert_utc_to_egypt(payment.payment_date)
                    if hasattr(egypt_time, 'hour'):
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day, 
                                            egypt_time.hour, egypt_time.minute, egypt_time.second)
                    else:
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day)
                    payment.payment_date = naive_time
                except Exception as e:
                    print(f"خطأ في تحويل payment_date للدفعة {payment.id}: {str(e)}")
            
            if payment.created_at:
                try:
                    egypt_time = convert_utc_to_egypt(payment.created_at)
                    if hasattr(egypt_time, 'hour'):
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day, 
                                            egypt_time.hour, egypt_time.minute, egypt_time.second)
                    else:
                        naive_time = datetime(egypt_time.year, egypt_time.month, egypt_time.day)
                    payment.created_at = naive_time
                except Exception as e:
                    print(f"خطأ في تحويل created_at للدفعة {payment.id}: {str(e)}")
        
        # حفظ التغييرات في قاعدة البيانات
        db.session.commit()
        print("تم تصحيح جميع التواريخ بنجاح!")

if __name__ == "__main__":
    fix_dates()