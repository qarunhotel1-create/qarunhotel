#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
حذف جميع الحجوزات من النظام مباشرة
"""

import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.payment import Payment

def delete_all_bookings():
    """حذف جميع الحجوزات والمدفوعات المرتبطة بها"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️ بدء حذف جميع الحجوزات...")
            
            # عد الحجوزات الموجودة
            total_bookings = Booking.query.count()
            total_payments = Payment.query.count()
            
            print(f"📊 الحجوزات الموجودة: {total_bookings}")
            print(f"📊 المدفوعات الموجودة: {total_payments}")
            
            if total_bookings == 0:
                print("ℹ️ لا توجد حجوزات للحذف")
                return
            
            # حذف جميع المدفوعات أولاً (بسبب العلاقات الخارجية)
            if total_payments > 0:
                print("🗑️ حذف جميع المدفوعات...")
                Payment.query.delete()
                print(f"✅ تم حذف {total_payments} مدفوعة")
            
            # حذف جميع الحجوزات
            print("🗑️ حذف جميع الحجوزات...")
            Booking.query.delete()
            
            # حفظ التغييرات
            db.session.commit()
            
            print(f"✅ تم حذف {total_bookings} حجز بنجاح")
            print("✅ تم حذف جميع الحجوزات والمدفوعات من النظام")
            
            # التحقق من النتيجة
            remaining_bookings = Booking.query.count()
            remaining_payments = Payment.query.count()
            
            print(f"\n📊 النتيجة النهائية:")
            print(f"   • الحجوزات المتبقية: {remaining_bookings}")
            print(f"   • المدفوعات المتبقية: {remaining_payments}")
            
            if remaining_bookings == 0 and remaining_payments == 0:
                print("\n🎉 تم حذف جميع البيانات بنجاح!")
            else:
                print("\n⚠️ تحذير: لم يتم حذف جميع البيانات")
                
        except Exception as e:
            print(f"❌ خطأ في حذف الحجوزات: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    delete_all_bookings()
