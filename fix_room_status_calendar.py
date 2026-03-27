#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح مشكلة عرض حالة الغرف في التقويم
المشكلة: الغرف تظهر كأنها محجوزة حتى بعد انتهاء فترة الحجز
الحل: تحديث منطق تحديد الحجز الحالي للغرفة وإضافة تحديث تلقائي لحالة الغرف
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Room, Booking
from hotel.utils.datetime_utils import get_egypt_now
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_

def fix_room_status_logic():
    """إصلاح منطق تحديد حالة الغرف"""
    
    app = create_app()
    with app.app_context():
        print("🔧 بدء إصلاح منطق حالة الغرف...")
        
        # الحصول على التاريخ والوقت الحالي بتوقيت مصر
        now = get_egypt_now()
        today = now.date()
        current_hour = now.hour
        
        print(f"📅 التاريخ الحالي: {today}")
        print(f"⏰ الوقت الحالي: {now.strftime('%H:%M')}")
        
        # جلب جميع الغرف
        rooms = Room.query.all()
        print(f"🏨 عدد الغرف الإجمالي: {len(rooms)}")
        
        updated_rooms = 0
        
        for room in rooms:
            old_status = room.status
            
            # البحث عن الحجوزات النشطة للغرفة
            active_bookings = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.status.in_(['confirmed', 'checked_in']),
                Booking.check_in_date <= today
            ).all()
            
            # تصفية الحجوزات بناءً على تاريخ المغادرة والوقت الحالي
            current_booking = None
            
            for booking in active_bookings:
                # منطق تحديد ما إذا كان الحجز ما زال نشطاً
                is_still_active = False
                
                if booking.status == 'checked_in':
                    # إذا كان النزيل مسجل دخول، نتحقق من تاريخ المغادرة
                    if current_hour < 12:
                        # قبل 12 ظهراً: نعتبر يوم المغادرة ما زال محجوزاً
                        is_still_active = booking.check_out_date >= today
                    else:
                        # بعد 12 ظهراً: يوم المغادرة يصبح متاحاً
                        is_still_active = booking.check_out_date > today
                
                elif booking.status == 'confirmed':
                    # الحجوزات المؤكدة تظهر فقط في يوم الدخول وبعد الساعة 1 ظهراً
                    if booking.check_in_date == today and current_hour >= 13:
                        if current_hour < 12:
                            is_still_active = booking.check_out_date >= today
                        else:
                            is_still_active = booking.check_out_date > today
                    elif booking.check_in_date < today:
                        # حجز مؤكد لم يتم تسجيل دخوله ومر موعده
                        if current_hour < 12:
                            is_still_active = booking.check_out_date >= today
                        else:
                            is_still_active = booking.check_out_date > today
                
                if is_still_active:
                    current_booking = booking
                    break
            
            # تحديث حالة الغرفة
            if current_booking:
                if current_booking.status == 'checked_in':
                    new_status = 'occupied'
                elif current_booking.status == 'confirmed':
                    new_status = 'reserved'
                else:
                    new_status = 'available'
            else:
                # لا يوجد حجز نشط، تأكد من أن الغرفة متاحة (إلا إذا كانت في صيانة)
                if room.status != 'maintenance':
                    new_status = 'available'
                else:
                    new_status = room.status  # احتفظ بحالة الصيانة
            
            # تحديث حالة الغرفة إذا تغيرت
            if room.status != new_status:
                room.status = new_status
                updated_rooms += 1
                print(f"🔄 غرفة {room.room_number}: {old_status} → {new_status}")
                
                if current_booking:
                    print(f"   📋 الحجز النشط: {current_booking.booking_code} ({current_booking.status})")
                    print(f"   📅 من {current_booking.check_in_date} إلى {current_booking.check_out_date}")
        
        # حفظ التغييرات
        if updated_rooms > 0:
            try:
                db.session.commit()
                print(f"✅ تم تحديث {updated_rooms} غرفة بنجاح")
            except Exception as e:
                db.session.rollback()
                print(f"❌ خطأ في حفظ التغييرات: {e}")
                return False
        else:
            print("ℹ️ لا توجد غرف تحتاج تحديث")
        
        # عرض الإحصائيات النهائية
        print("\n📊 الإحصائيات النهائية:")
        available_count = Room.query.filter_by(status='available').count()
        occupied_count = Room.query.filter_by(status='occupied').count()
        reserved_count = Room.query.filter_by(status='reserved').count()
        maintenance_count = Room.query.filter_by(status='maintenance').count()
        
        print(f"🟢 متاحة: {available_count}")
        print(f"🔴 مشغولة: {occupied_count}")
        print(f"🟡 محجوزة: {reserved_count}")
        print(f"🔧 صيانة: {maintenance_count}")
        
        return True

def create_room_status_update_function():
    """إنشاء دالة لتحديث حالة الغرف تلقائياً"""
    
    # إنشاء ملف دالة التحديث التلقائي
    update_function_code = '''
def update_room_statuses():
    """تحديث حالة الغرف تلقائياً بناءً على الحجوزات النشطة"""
    from hotel.models import Room, Booking
    from hotel.utils.datetime_utils import get_egypt_now
    from hotel import db
    from datetime import date
    
    now = get_egypt_now()
    today = now.date()
    current_hour = now.hour
    
    rooms = Room.query.all()
    
    for room in rooms:
        # البحث عن الحجوزات النشطة للغرفة
        active_bookings = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.status.in_(['confirmed', 'checked_in']),
            Booking.check_in_date <= today
        ).all()
        
        # تصفية الحجوزات بناءً على تاريخ المغادرة والوقت الحالي
        current_booking = None
        
        for booking in active_bookings:
            is_still_active = False
            
            if booking.status == 'checked_in':
                if current_hour < 12:
                    is_still_active = booking.check_out_date >= today
                else:
                    is_still_active = booking.check_out_date > today
            
            elif booking.status == 'confirmed':
                if booking.check_in_date == today and current_hour >= 13:
                    if current_hour < 12:
                        is_still_active = booking.check_out_date >= today
                    else:
                        is_still_active = booking.check_out_date > today
                elif booking.check_in_date < today:
                    if current_hour < 12:
                        is_still_active = booking.check_out_date >= today
                    else:
                        is_still_active = booking.check_out_date > today
            
            if is_still_active:
                current_booking = booking
                break
        
        # تحديث حالة الغرفة
        if current_booking:
            if current_booking.status == 'checked_in':
                new_status = 'occupied'
            elif current_booking.status == 'confirmed':
                new_status = 'reserved'
            else:
                new_status = 'available'
        else:
            if room.status != 'maintenance':
                new_status = 'available'
            else:
                new_status = room.status
        
        room.status = new_status
    
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في تحديث حالة الغرف: {e}")
        return False
'''
    
    # كتابة الدالة في ملف منفصل
    with open('e:\\1\\QARUN HOTEL\\hotel\\utils\\room_status_updater.py', 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""\nدالة تحديث حالة الغرف تلقائياً\n"""\n\n')
        f.write(update_function_code)
    
    print("✅ تم إنشاء دالة التحديث التلقائي في hotel/utils/room_status_updater.py")

def update_room_model():
    """تحديث نموذج الغرفة لتحسين منطق current_booking"""
    
    print("🔧 تحديث نموذج الغرفة...")
    
    # قراءة الملف الحالي
    room_model_path = 'e:\\1\\QARUN HOTEL\\hotel\\models\\room.py'
    
    with open(room_model_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # البحث عن دالة current_booking وتحديثها
    new_current_booking_method = '''    @property
    def current_booking(self):
        """الحصول على الحجز الحالي للغرفة (محسّن)
        - قبل 12 PM: نعتبر يوم المغادرة محجوزاً
        - بعد 12 PM: يوم المغادرة يصبح متاحاً
        - الحجوزات المؤكدة تظهر فقط في يوم الدخول وبعد 1 PM
        """
        from hotel.models.booking import Booking, BOOKING_STATUS_CHECKED_IN, BOOKING_STATUS_CONFIRMED
        from datetime import date
        from hotel.utils.datetime_utils import get_egypt_now
        from sqlalchemy import and_, or_

        now = get_egypt_now()
        today = now.date()
        current_hour = now.hour

        # البحث عن الحجوزات النشطة
        active_bookings = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status.in_([BOOKING_STATUS_CHECKED_IN, BOOKING_STATUS_CONFIRMED]),
            Booking.check_in_date <= today
        ).all()

        # تصفية الحجوزات بناءً على المنطق المحسّن
        for booking in active_bookings:
            is_still_active = False
            
            if booking.status == BOOKING_STATUS_CHECKED_IN:
                # النزلاء المسجلين: نتحقق من تاريخ المغادرة
                if current_hour < 12:
                    is_still_active = booking.check_out_date >= today
                else:
                    is_still_active = booking.check_out_date > today
            
            elif booking.status == BOOKING_STATUS_CONFIRMED:
                # الحجوزات المؤكدة: تظهر في يوم الدخول بعد 1 PM
                if booking.check_in_date == today and current_hour >= 13:
                    if current_hour < 12:
                        is_still_active = booking.check_out_date >= today
                    else:
                        is_still_active = booking.check_out_date > today
                elif booking.check_in_date < today:
                    # حجز مؤكد لم يتم تسجيل دخوله
                    if current_hour < 12:
                        is_still_active = booking.check_out_date >= today
                    else:
                        is_still_active = booking.check_out_date > today
            
            if is_still_active:
                return booking
        
        return None'''
    
    # استبدال الدالة القديمة بالجديدة
    import re
    
    # البحث عن بداية ونهاية دالة current_booking
    pattern = r'(\s+@property\s+def current_booking\(self\):.*?return query\.first\(\))'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_current_booking_method, content, flags=re.DOTALL)
        
        # كتابة الملف المحدث
        with open(room_model_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ تم تحديث نموذج الغرفة بنجاح")
        return True
    else:
        print("⚠️ لم يتم العثور على دالة current_booking لتحديثها")
        return False

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء إصلاح مشكلة عرض حالة الغرف في التقويم")
    print("=" * 60)
    
    try:
        # 1. إصلاح حالة الغرف الحالية
        print("\n1️⃣ إصلاح حالة الغرف الحالية...")
        if not fix_room_status_logic():
            print("❌ فشل في إصلاح حالة الغرف")
            return False
        
        # 2. إنشاء دالة التحديث التلقائي
        print("\n2️⃣ إنشاء دالة التحديث التلقائي...")
        create_room_status_update_function()
        
        # 3. تحديث نموذج الغرفة
        print("\n3️⃣ تحديث نموذج الغرفة...")
        update_room_model()
        
        print("\n" + "=" * 60)
        print("✅ تم إصلاح مشكلة عرض حالة الغرف بنجاح!")
        print("\n📋 ملخص الإصلاحات:")
        print("   • تم تحديث حالة الغرف الحالية")
        print("   • تم إنشاء دالة التحديث التلقائي")
        print("   • تم تحسين منطق تحديد الحجز الحالي")
        print("\n💡 نصائح:")
        print("   • سيتم تحديث حالة الغرف تلقائياً عند عرض لوحة التحكم")
        print("   • بعد 12 ظهراً، الغرف التي انتهت فترة حجزها ستصبح متاحة")
        print("   • الحجوزات المؤكدة ستظهر فقط في يوم الدخول بعد 1 ظهراً")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تنفيذ الإصلاح: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()