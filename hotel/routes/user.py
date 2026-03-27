from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from hotel.models import Booking, Customer, Room, Payment
from sqlalchemy import or_, func
from datetime import datetime, timedelta

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """لوحة تحكم المستخدم العادي"""
    # التحقق من أن المستخدم ليس admin
    if current_user.has_permission('admin'):
        # إعادة توجيه admin إلى لوحة التحكم الخاصة به
        from flask import redirect, url_for
        return redirect(url_for('admin.dashboard'))
    
    # حساب الإحصائيات
    stats = {}
    
    if current_user.has_permission('manage_bookings'):
        # إحصائيات شاملة للمستخدمين الذين لديهم صلاحية إدارة الحجوزات
        stats['total_bookings'] = Booking.query.count()
        stats['active_bookings'] = Booking.query.filter(
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
        stats['pending_bookings'] = Booking.query.filter_by(status='pending').count()
        
        # حساب إجمالي الإيرادات
        total_revenue = Payment.query.with_entities(func.sum(Payment.amount)).scalar() or 0
        stats['total_revenue'] = total_revenue
        
        # آخر الحجوزات
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    else:
        # إحصائيات محدودة للمستخدمين العاديين (حجوزاتهم فقط)
        user_bookings = Booking.query.filter_by(user_id=current_user.id)
        stats['total_bookings'] = user_bookings.count()
        stats['active_bookings'] = user_bookings.filter(
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
        stats['pending_bookings'] = user_bookings.filter_by(status='pending').count()
        
        # حساب إيرادات حجوزات المستخدم فقط
        user_payments = Payment.query.join(Booking).filter(Booking.user_id == current_user.id)
        total_revenue = user_payments.with_entities(func.sum(Payment.amount)).scalar() or 0
        stats['total_revenue'] = total_revenue
        
        # آخر حجوزات المستخدم
        recent_bookings = user_bookings.order_by(Booking.created_at.desc()).limit(5).all()

    # بيانات الغرف لخريطة الغرف مع الحجوزات الحالية
    from sqlalchemy.orm import joinedload
    from datetime import date, timedelta

    # تحديث حالة الغرف تلقائياً
    try:
        from hotel.utils.room_status_updater import update_room_statuses
        update_room_statuses()
    except Exception as e:
        print(f"خطأ في تحديث حالة الغرف: {e}")

    rooms = Room.query.order_by(Room.room_number).all()

    # منطق عرض خريطة الغرف: أي حجز نشط اليوم يجب أن يمنع إتاحة الغرفة للحجز
    from hotel.utils.datetime_utils import get_egypt_now
    now = get_egypt_now()
    today = now.date()

    # الغرف ذات نزيل مسجل دخول فعليًا الآن (تعتبر مشغولة دائماً)
    checked_in_room_ids = set(
        rid for (rid,) in Booking.query.with_entities(Booking.room_id)
        .filter(
            Booking.status == 'checked_in',
            Booking.check_in_date <= today,
            Booking.check_out_date >= today
        )
        .all()
    )

    # مجموعات لمعرفة وضع الغرف بالنسبة للحجوزات المؤكدة مع سياسة 12 ظهرًا
    from sqlalchemy import and_

    # حجز يبدأ اليوم
    confirmed_start_today_ids = set(
        rid for (rid,) in Booking.query.with_entities(Booking.room_id)
        .filter(
            Booking.status == 'confirmed',
            Booking.check_in_date == today
        )
        .all()
    )

    # حجز في منتصف الإقامة (اليوم بين الدخول والخروج)
    confirmed_mid_ids = set(
        rid for (rid,) in Booking.query.with_entities(Booking.room_id)
        .filter(
            Booking.status == 'confirmed',
            Booking.check_in_date < today,
            Booking.check_out_date > today
        )
        .all()
    )

    # حجز يغادر اليوم
    confirmed_end_today_ids = set(
        rid for (rid,) in Booking.query.with_entities(Booking.room_id)
        .filter(
            Booking.status == 'confirmed',
            Booking.check_out_date == today
        )
        .all()
    )

    hour = now.hour

    # إنشاء حالة عرض ديناميكية لكل غرفة وفق سياسة 12 ظهرًا مع فضّ التعارض بين دخول وخروج في نفس اليوم
    display_statuses = {}
    for r in rooms:
        status = r.status
        # الغرف المسجل دخول بها تظهر مشغولة دائماً
        if r.id in checked_in_room_ids:
            display_statuses[r.id] = 'occupied'
        # منتصف الإقامة المؤكدة: محجوزة طوال اليوم
        elif r.id in confirmed_mid_ids:
            display_statuses[r.id] = 'reserved'
        # إذا كان هناك خروج اليوم ودخول اليوم لنفس الغرفة: تبقى محجوزة طوال اليوم (قبل وبعد 12)
        elif (r.id in confirmed_end_today_ids) and (r.id in confirmed_start_today_ids):
            display_statuses[r.id] = 'reserved'
        # يغادر اليوم فقط: قبل 12 محجوزة، بعد 12 متاحة
        elif r.id in confirmed_end_today_ids:
            display_statuses[r.id] = 'reserved' if hour < 12 else 'available'
        # يبدأ اليوم فقط: قبل 12 متاحة، من 12 فما بعد محجوزة
        elif r.id in confirmed_start_today_ids:
            display_statuses[r.id] = 'reserved' if hour >= 12 else 'available'
        else:
            display_statuses[r.id] = status

    # إحصائيات العناوين حسب حالة العرض
    available_count = sum(1 for s in display_statuses.values() if s == 'available')
    occupied_count = sum(1 for s in display_statuses.values() if s == 'occupied')
    reserved_count = sum(1 for s in display_statuses.values() if s == 'reserved')

    # تحديد الحجز المعروض لكل غرفة وفق سياسة 12 ظهرًا
    room_display_bookings = {}
    for r in rooms:
        ds = display_statuses.get(r.id, r.status)
        display_booking = None
        if ds == 'occupied':
            # إظهار آخر حجز مسجل دخول اليوم
            display_booking = (
                Booking.query.filter(
                    Booking.room_id == r.id,
                    Booking.status == 'checked_in',
                    Booking.check_in_date <= today,
                    Booking.check_out_date >= today
                ).order_by(Booking.id.desc()).first()
            )
        elif ds == 'reserved':
            if hour >= 12:
                # من 12 ظهرًا فأكثر نعرض حجز اليوم (العميل التالي)
                display_booking = (
                    Booking.query.filter(
                        Booking.room_id == r.id,
                        Booking.status == 'confirmed',
                        Booking.check_in_date == today
                    ).order_by(Booking.id.asc()).first()
                )
                if not display_booking:
                    # أو حجز مؤكد في منتصف الإقامة
                    display_booking = (
                        Booking.query.filter(
                            Booking.room_id == r.id,
                            Booking.status == 'confirmed',
                            Booking.check_in_date < today,
                            Booking.check_out_date > today
                        ).order_by(Booking.id.desc()).first()
                    )
            else:
                # قبل 12 ظهرًا نُظهر الحجز الجاري (منتصف إقامة)
                display_booking = (
                    Booking.query.filter(
                        Booking.room_id == r.id,
                        Booking.status == 'confirmed',
                        Booking.check_in_date < today,
                        Booking.check_out_date > today
                    ).order_by(Booking.id.desc()).first()
                )
        # غير ذلك: لا نعرض تفاصيل حجز
        room_display_bookings[r.id] = display_booking

    # بناء تقويم 30 يوم من اليوم (بتوقيت مصر)
    start_date = now.date()
    end_date = start_date + timedelta(days=30)
    calendar_dates = [start_date + timedelta(days=i) for i in range(30)]

    # جلب الحجوزات النشطة للتقويم
    # المنطق البسيط: الحجز نشط من يوم الدخول حتى اليوم السابق للمغادرة
    from sqlalchemy import and_, or_
    
    # الحجوزات التي تتقاطع مع نطاق التقويم
    active_bookings = Booking.query.filter(
        Booking.check_in_date < end_date,  # يبدأ قبل نهاية النطاق
        Booking.check_out_date > start_date,  # ينتهي بعد بداية النطاق
        Booking.status.in_(['confirmed', 'checked_in'])
    ).all()

    # تجميع الحجوزات حسب الغرفة
    bookings_by_room = {}
    for b in active_bookings:
        bookings_by_room.setdefault(b.room_id, []).append(b)

    def get_booking_for_day(bookings_list, day):
        """الحصول على الحجز النشط في يوم معين
        المنطق: الحجز نشط من يوم الدخول حتى اليوم السابق للمغادرة
        مثال: حجز من 27/8 إلى 28/8 يعني محجوز في 27/8 فقط، متاح في 28/8
        """
        for b in bookings_list:
            # الحجز نشط إذا كان اليوم >= يوم الدخول و < يوم المغادرة
            if b.check_in_date <= day < b.check_out_date:
                return b
        return None

    room_calendar = []
    for r in rooms:
        bks = bookings_by_room.get(r.id, [])
        statuses = []
        booking_codes = []
        
        for d in calendar_dates:
            booking = get_booking_for_day(bks, d)
            if booking:
                statuses.append('booked')
                booking_codes.append(booking.booking_code or str(booking.id))
            else:
                statuses.append('available')
                booking_codes.append(None)
        
        room_calendar.append({
            'room_id': r.id,
            'room_number': r.room_number,
            'statuses': statuses,
            'booking_codes': booking_codes
        })

    return render_template('user/dashboard.html',
                         title='لوحة التحكم',
                         stats=stats,
                         recent_bookings=recent_bookings,
                         rooms=rooms,
                         calendar_dates=calendar_dates,
                         room_calendar=room_calendar,
                         now=now,
                         display_statuses=display_statuses,
                         available_count=available_count,
                         occupied_count=occupied_count,
                         reserved_count=reserved_count,
                         room_display_bookings=room_display_bookings)

@user_bp.route('/search-bookings')
@login_required
def search_bookings():
    """البحث الذكي في الحجوزات للمستخدم العادي"""
    query = request.args.get('q', '').strip()
    is_ajax = request.args.get('ajax') == '1'

    if not query:
        if is_ajax:
            return jsonify({
                'success': True,
                'count': 0,
                'results': [],
                'query': query
            })
        return jsonify({'bookings': []})

    try:
        # تحديد نطاق البحث حسب صلاحيات المستخدم
        if current_user.has_permission('manage_bookings'):
            # البحث في جميع الحجوزات
            bookings_query = Booking.query.join(Customer).join(Room)
        else:
            # البحث في حجوزات المستخدم فقط
            bookings_query = Booking.query.join(Customer).join(Room).filter(Booking.user_id == current_user.id)

        bookings = []

        # البحث الدقيق والمحدد (نفس منطق admin)
        if query.isdigit():
            booking_id = int(query)
            bookings = []
            
            # 1. البحث كترقيم سنوي (الأولوية كما طلب المستخدم لعرض كل السنوات)
            seq_matches = bookings_query.filter(Booking.year_seq == booking_id).order_by(Booking.created_at.desc()).all()
            if seq_matches:
                bookings.extend(seq_matches)
            
            # 2. البحث برقم المعرف الفريد (ID)
            id_match = bookings_query.filter(Booking.id == booking_id).first()
            if id_match:
                # التأكد من عدم التكرار
                exists = False
                for b in bookings:
                    if b.id == id_match.id:
                        exists = True
                        break
                if not exists:
                    bookings.append(id_match)
            
            # 3. إذا لم يوجد أي نتائج رقمية، ابحث في الهواتف وأرقام الهوية
            if not bookings:
                bookings = bookings_query.filter(
                    or_(
                        Customer.phone == query,
                        Customer.id_number == query,
                        Room.room_number == query
                    )
                ).order_by(Booking.created_at.desc()).all()
        else:
            # البحث النصي الدقيق
            exact_name_bookings = bookings_query.filter(
                Customer.name.ilike(f'{query}')
            ).order_by(Booking.created_at.desc()).all()

            if exact_name_bookings:
                bookings = exact_name_bookings
            else:
                if len(query) >= 2:
                    partial_name_bookings = bookings_query.filter(
                        Customer.name.ilike(f'%{query}%')
                    ).order_by(Booking.created_at.desc()).all()

                    if partial_name_bookings:
                        bookings = partial_name_bookings
                    else:
                        bookings = bookings_query.filter(
                            or_(
                                Customer.phone.ilike(f'%{query}%'),
                                Customer.id_number.ilike(f'%{query}%')
                            )
                        ).order_by(Booking.created_at.desc()).all()

        # تحويل النتائج إلى JSON
        results = []
        for booking in bookings:
            try:
                results.append({
                    'id': booking.id,
                    'booking_code': booking.booking_code,
                    'booking_year': booking.booking_year,
                    'year_seq': booking.year_seq,
                    'customer_name': booking.customer.name,
                    'customer_phone': booking.customer.phone or '',
                    'customer_id_number': booking.customer.id_number or '',
                    'room_number': booking.room.room_number,
                    'status': booking.status,
                    'status_display': booking.get_status_display(),
                    'check_in': booking.check_in_date.strftime('%Y-%m-%d') if booking.check_in_date else '',
                    'check_out': booking.check_out_date.strftime('%Y-%m-%d') if booking.check_out_date else '',
                    'total_price': float(booking.total_price or 0),
                    'url': url_for('booking.details', id=booking.id)
                })
            except Exception as e:
                print(f"خطأ في معالجة الحجز {booking.id}: {e}")
                continue

        if is_ajax:
            return jsonify({
                'success': True,
                'count': len(results),
                'results': results,
                'query': query
            })
        else:
            # للتوافق مع النظام القديم
            return jsonify({'bookings': results})

    except Exception as e:
        print(f"خطأ في البحث: {e}")
        if is_ajax:
            return jsonify({
                'success': False,
                'error': str(e),
                'count': 0,
                'results': []
            })
        return jsonify({'bookings': []})

@user_bp.route('/quick-stats')
@login_required
def quick_stats():
    """إحصائيات سريعة للمستخدم"""
    today = datetime.now().date()
    
    if current_user.has_permission('manage_bookings'):
        # إحصائيات شاملة
        today_checkins = Booking.query.filter(
            Booking.check_in_date == today,
            Booking.status == 'confirmed'
        ).count()
        
        today_checkouts = Booking.query.filter(
            Booking.check_out_date == today,
            Booking.status == 'checked_in'
        ).count()
        
        pending_payments = Booking.query.filter(
            Booking.remaining_amount > 0,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
    else:
        # إحصائيات محدودة
        user_bookings = Booking.query.filter_by(user_id=current_user.id)
        
        today_checkins = user_bookings.filter(
            Booking.check_in_date == today,
            Booking.status == 'confirmed'
        ).count()
        
        today_checkouts = user_bookings.filter(
            Booking.check_out_date == today,
            Booking.status == 'checked_in'
        ).count()
        
        pending_payments = user_bookings.filter(
            Booking.remaining_amount > 0,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
    
    return jsonify({
        'today_checkins': today_checkins,
        'today_checkouts': today_checkouts,
        'pending_payments': pending_payments
    })

@user_bp.route('/test-search')
@login_required
def test_search():
    """صفحة اختبار البحث"""
    return render_template('test_search.html', title='اختبار البحث')
