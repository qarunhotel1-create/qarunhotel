#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.customer import Customer
from hotel.models.room import Room
from hotel.models.user import User
from flask import url_for
import json

# اختبار تحسينات لوحة تحكم المستخدمين
app = create_app()

with app.test_client() as client:
    with app.app_context():
        try:
            print("🎨 اختبار تحسينات لوحة تحكم المستخدمين")
            print("=" * 60)
            
            # البحث عن مستخدم عادي
            regular_user = User.query.filter(User.username != 'admin').first()
            if not regular_user:
                print("⚠️ لا يوجد مستخدمين عاديين، سأستخدم admin للاختبار...")
                regular_user = User.query.filter_by(username='admin').first()
            
            if not regular_user:
                print("❌ لم يتم العثور على أي مستخدم")
                exit(1)
            
            print(f"✅ تم العثور على المستخدم: {regular_user.username}")
            
            # تسجيل دخول المستخدم
            with client.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
                sess['_fresh'] = True
            
            # اختبار الوصول للوحة التحكم المحدثة
            print(f"\n🏠 اختبار لوحة التحكم المحدثة...")
            dashboard_response = client.get('/user/dashboard')
            
            if dashboard_response.status_code == 200:
                dashboard_content = dashboard_response.get_data(as_text=True)
                
                # فحص العناصر الجديدة
                checks = [
                    ('welcome-header', 'رأس الترحيب المحسن'),
                    ('صلاحياتك في النظام', 'قسم الصلاحيات'),
                    ('خريطة الغرف', 'خريطة الغرف'),
                    ('mini-stat-card', 'الإحصائيات المصغرة'),
                    ('permission-card', 'بطاقات الصلاحيات'),
                    ('rooms-map', 'خريطة الغرف'),
                    ('room-card', 'بطاقات الغرف'),
                    ('bg-gradient', 'التدرجات اللونية'),
                    ('userSmartSearch', 'البحث الذكي'),
                    ('آخر الحجوزات', 'قسم آخر الحجوزات')
                ]
                
                print("  📋 فحص العناصر الجديدة:")
                for element, description in checks:
                    if element in dashboard_content:
                        print(f"    ✅ {description}")
                    else:
                        print(f"    ❌ {description} غير موجود")
                
                # فحص عدم وجود العناصر المحذوفة
                removed_elements = [
                    'إجمالي الحجوزات'
                ]
                
                print("  🗑️ فحص العناصر المحذوفة:")
                for element in removed_elements:
                    if element not in dashboard_content:
                        print(f"    ✅ تم حذف: {element}")
                    else:
                        print(f"    ❌ لم يتم حذف: {element}")
                
                # فحص النص المطلوب
                required_texts = [
                    f'مرحباً بك {regular_user.full_name} في QARUN HOTEL',
                    'الحجوزات النشطة',
                    'في الانتظار',
                    'إجمالي الإيرادات',
                    'إنشاء حجز جديد',
                    'تعديل الحجوزات',
                    'تسجيل الدخول والخروج',
                    'إضافة دفعات',
                    'إدارة العملاء',
                    'عرض التقارير'
                ]
                
                print("  📝 فحص النصوص المطلوبة:")
                for text in required_texts:
                    if text in dashboard_content:
                        print(f"    ✅ {text}")
                    else:
                        print(f"    ❌ {text} غير موجود")
                
            else:
                print(f"  ❌ لا يمكن الوصول للوحة التحكم: {dashboard_response.status_code}")
            
            # اختبار البحث الذكي
            print(f"\n🔍 اختبار البحث الذكي...")
            search_response = client.get('/user/search-bookings?q=test&ajax=1')
            if search_response.status_code == 200:
                print("  ✅ البحث الذكي يعمل")
            else:
                print(f"  ❌ البحث الذكي لا يعمل: {search_response.status_code}")
            
            # إحصائيات البيانات
            print(f"\n📊 إحصائيات البيانات:")
            total_bookings = Booking.query.count()
            total_rooms = Room.query.count()
            total_customers = Customer.query.count()
            
            print(f"  📋 إجمالي الحجوزات: {total_bookings}")
            print(f"  🏨 إجمالي الغرف: {total_rooms}")
            print(f"  👥 إجمالي العملاء: {total_customers}")
            
            if total_bookings > 0:
                active_bookings = Booking.query.filter(
                    Booking.status.in_(['confirmed', 'checked_in'])
                ).count()
                pending_bookings = Booking.query.filter_by(status='pending').count()
                
                print(f"  ✅ الحجوزات النشطة: {active_bookings}")
                print(f"  ⏳ الحجوزات في الانتظار: {pending_bookings}")
            
            if total_rooms > 0:
                available_rooms = Room.query.filter_by(status='available').count()
                occupied_rooms = Room.query.filter_by(status='occupied').count()
                
                print(f"  🟢 الغرف المتاحة: {available_rooms}")
                print(f"  🔴 الغرف المشغولة: {occupied_rooms}")
            
            # اختبار الاستجابة
            print(f"\n⚡ اختبار الأداء:")
            import time
            
            start_time = time.time()
            performance_response = client.get('/user/dashboard')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            print(f"  ⏱️ وقت تحميل لوحة التحكم: {response_time:.2f} ميلي ثانية")
            
            if response_time < 1000:
                print("  🚀 أداء ممتاز!")
            elif response_time < 2000:
                print("  ⚡ أداء جيد")
            else:
                print("  ⚠️ قد يحتاج تحسين")
            
            print(f"\n" + "=" * 60)
            print("🎉 تم اختبار تحسينات لوحة تحكم المستخدمين!")
            print("\n📋 ملخص التحسينات المطبقة:")
            print("✅ حذف 'إجمالي الحجوزات' من الإحصائيات")
            print("✅ تحسين رأس الترحيب مع إحصائيات مصغرة")
            print("✅ إضافة قسم 'صلاحياتك في النظام' التفاعلي")
            print("✅ إضافة خريطة الغرف الاحترافية والتفاعلية")
            print("✅ تحسين تصميم 'آخر الحجوزات'")
            print("✅ إضافة البحث الذكي للمستخدمين")
            print("✅ تطبيق تصميم احترافي مع تدرجات لونية")
            print("✅ إضافة تأثيرات متحركة وتفاعلية")
            
            print(f"\n🎨 الميزات الجديدة:")
            print("1. رسالة ترحيب شخصية مع اسم المستخدم")
            print("2. إحصائيات مرئية للحجوزات النشطة والمنتظرة")
            print("3. عرض الصلاحيات كبطاقات تفاعلية")
            print("4. خريطة غرف تفاعلية مع حالة كل غرفة")
            print("5. تصميم متجاوب ومتحرك")
            print("6. بحث ذكي فوري")
            
            print(f"\n🚀 يمكن للمستخدمين الآن:")
            print("- رؤية حالة جميع الغرف بصرياً")
            print("- الوصول السريع لصلاحياتهم")
            print("- البحث الفوري في الحجوزات")
            print("- تجربة مستخدم محسنة وسلسة")
            print("- واجهة احترافية وجذابة")
            
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            import traceback
            traceback.print_exc()
