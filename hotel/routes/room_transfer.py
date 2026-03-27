from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import and_

from hotel import db
from hotel.models import Booking, Room, RoomTransfer
from hotel.forms.room_transfer import RoomTransferForm
from hotel.utils.decorators import permission_required
from hotel.utils.activity_logger import log_activity

room_transfer_bp = Blueprint('room_transfer', __name__, url_prefix='/room-transfer')

@room_transfer_bp.route('/booking/<int:booking_id>')
@login_required
@permission_required('manage_bookings')
def transfer_form(booking_id):
    """صفحة نقل العميل"""
    booking = Booking.query.get_or_404(booking_id)
    
    # التحقق من أن الحجز في حالة تسجيل دخول
    if booking.status != 'checked_in':
        flash('يمكن نقل العميل فقط عندما يكون في حالة تسجيل دخول', 'error')
        return redirect(url_for('booking.details', id=booking_id))
    
    form = RoomTransferForm()
    
    # الحصول على الغرف المتاحة (باستثناء الغرفة الحالية)
    # ملاحظة: نعتمد على عدم وجود حجز نشط اليوم، وليس على status فقط لتجنب بقاء حالة الغرفة قديمًا
    from datetime import date
    from hotel.utils.datetime_utils import get_egypt_now
    now = get_egypt_now()
    cutoff_passed = now.hour >= 13

    # الغرف التي لديها حجز نشط اليوم باحترام حد 1 ظهرًا
    active_query = db.session.query(Booking.room_id).filter(
        Booking.status.in_(['confirmed', 'checked_in']),
        Booking.check_in_date <= date.today(),
    )
    if cutoff_passed:
        active_query = active_query.filter(Booking.check_out_date > date.today())
    else:
        active_query = active_query.filter(Booking.check_out_date >= date.today())

    active_rooms_subq = active_query.subquery()

    available_rooms = Room.query.filter(
        Room.id != booking.room_id,             # استثناء الغرفة الحالية
        Room.status != 'maintenance',           # استثناء غرف الصيانة
        ~Room.id.in_(active_rooms_subq)         # لا يوجد حجز نشط اليوم لهذه الغرفة
    ).order_by(Room.room_number).all()
    
    form.to_room_id.choices = [(room.id, f'غرفة {room.room_number} - {room.room_type}')
                               for room in available_rooms]

    # تعيين القيمة الافتراضية لنوع الإقامة
    if not form.new_occupancy_type.data:
        form.new_occupancy_type.data = booking.occupancy_type

    return render_template('room_transfer/transfer_form.html',
                         booking=booking, form=form, available_rooms=available_rooms)

@room_transfer_bp.route('/booking/<int:booking_id>/execute', methods=['POST'])
@login_required
@permission_required('manage_bookings')
def execute_transfer(booking_id):
    """تنفيذ نقل العميل"""
    booking = Booking.query.get_or_404(booking_id)
    form = RoomTransferForm()
    
    # الحصول على الغرف المتاحة
    from datetime import date
    from hotel.utils.datetime_utils import get_egypt_now
    now = get_egypt_now()
    cutoff_passed = now.hour >= 13

    active_query = db.session.query(Booking.room_id).filter(
        Booking.status.in_(['confirmed', 'checked_in']),
        Booking.check_in_date <= date.today(),
    )
    if cutoff_passed:
        active_query = active_query.filter(Booking.check_out_date > date.today())
    else:
        active_query = active_query.filter(Booking.check_out_date >= date.today())

    active_rooms_subq = active_query.subquery()

    available_rooms = Room.query.filter(
        Room.id != booking.room_id,
        Room.status != 'maintenance',
        ~Room.id.in_(active_rooms_subq)
    ).order_by(Room.room_number).all()
    
    form.to_room_id.choices = [(room.id, f'غرفة {room.room_number} - {room.room_type}') 
                               for room in available_rooms]
    
    if form.validate_on_submit():
        try:
            # الحصول على الغرفة الجديدة
            new_room = Room.query.get(form.to_room_id.data)
            old_room = booking.room
            
            if not new_room:
                flash('الغرفة المحددة غير موجودة', 'error')
                return redirect(url_for('room_transfer.transfer_form', booking_id=booking_id))
            
            # تحقق من حالة الصيانة
            if new_room.status == 'maintenance':
                flash('الغرفة المحددة تحت الصيانة', 'error')
                return redirect(url_for('room_transfer.transfer_form', booking_id=booking_id))

            # تحقق من عدم وجود حجز نشط اليوم لهذه الغرفة (بدل الاعتماد على status فقط)
            from datetime import date
            from hotel.utils.datetime_utils import get_egypt_now
            now = get_egypt_now()
            cutoff_passed = now.hour >= 13

            conflict_query = Booking.query.filter(
                Booking.room_id == new_room.id,
                Booking.status.in_(['confirmed', 'checked_in']),
                Booking.check_in_date <= date.today(),
            )
            if cutoff_passed:
                conflict_query = conflict_query.filter(Booking.check_out_date > date.today())
            else:
                conflict_query = conflict_query.filter(Booking.check_out_date >= date.today())

            conflict = conflict_query.first()

            if conflict:
                flash('الغرفة المحددة غير متاحة اليوم (يوجد حجز نشط).', 'error')
                return redirect(url_for('room_transfer.transfer_form', booking_id=booking_id))
            
            # إنشاء سجل النقل
            current_time = datetime.now()
            # وقت الدخول للغرفة السابقة: استخدم وقت تسجيل الدخول الفعلي إن وُجد، وإلا بداية يوم تاريخ الدخول
            check_in_dt = booking.check_in_time or datetime.combine(booking.check_in_date, datetime.min.time())
            transfer_created = False

            # محاولة إنشاء السجل باستخدام SQL مباشر (أكثر أماناً)
            try:
                from sqlalchemy import text
                sql = text("""
                    INSERT INTO room_transfers
                    (booking_id, from_room_id, to_room_id, from_room_check_in, from_room_check_out,
                     to_room_check_in, transfer_date, transfer_time, transferred_by, transferred_by_user_id, reason, notes)
                    VALUES (:booking_id, :from_room_id, :to_room_id, :from_room_check_in,
                            :from_room_check_out, :to_room_check_in, :transfer_date, :transfer_time,
                            :transferred_by, :transferred_by_user_id, :reason, :notes)
                """)
                db.session.execute(sql, {
                    'booking_id': booking.id,
                    'from_room_id': old_room.id,
                    'to_room_id': new_room.id,
                    'from_room_check_in': check_in_dt,
                    'from_room_check_out': current_time,
                    'to_room_check_in': current_time,
                    'transfer_date': current_time,
                    'transfer_time': current_time,
                    'transferred_by': current_user.username,
                    'transferred_by_user_id': current_user.id,
                    'reason': form.reason.data or '',
                    'notes': form.notes.data or ''
                })
                transfer_created = True
            except Exception as e:
                # إذا فشل SQL المباشر، جرب ORM
                try:
                    transfer = RoomTransfer(
                        booking_id=booking.id,
                        from_room_id=old_room.id,
                        to_room_id=new_room.id,
                        from_room_check_in=check_in_dt,
                        from_room_check_out=current_time,
                        to_room_check_in=current_time,
                        transfer_date=current_time,
                        transfer_time=current_time,
                        transferred_by=current_user.username,
                        transferred_by_user_id=current_user.id,
                        reason=form.reason.data,
                        notes=form.notes.data
                    )
                    db.session.add(transfer)
                    transfer_created = True
                except Exception as orm_error:
                    raise Exception(f"فشل في إنشاء سجل النقل: {str(e)} | {str(orm_error)}")
            
            # تحديث الحجز
            booking.room_id = new_room.id

            # تحديث نوع الإقامة إذا تم تغييره
            if form.new_occupancy_type.data:
                booking.occupancy_type = form.new_occupancy_type.data
            
            # تحديث حالة الغرف
            old_room.status = 'available'
            new_room.status = 'occupied'
            
            # حفظ التغييرات
            if transfer_created:
                db.session.commit()
            else:
                raise Exception("فشل في إنشاء سجل النقل")
            
            # تسجيل النشاط
            log_activity(current_user, 'room_transfer', 
                        f'Transferred customer {booking.customer.name} from room {old_room.room_number} to room {new_room.room_number}')
            
            flash(f'تم نقل العميل بنجاح من غرفة {old_room.room_number} إلى غرفة {new_room.room_number}', 'success')
            return redirect(url_for('booking.details', id=booking_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء النقل: {str(e)}', 'error')
            return redirect(url_for('room_transfer.transfer_form', booking_id=booking_id))
    
    # إذا كان النموذج غير صحيح
    return render_template('room_transfer/transfer_form.html', 
                         booking=booking, form=form, available_rooms=available_rooms)

@room_transfer_bp.route('/booking/<int:booking_id>/history')
@login_required
@permission_required('manage_bookings')
def transfer_history(booking_id):
    """عرض تاريخ نقل العميل"""
    booking = Booking.query.get_or_404(booking_id)
    
    transfers = RoomTransfer.query.filter_by(
        booking_id=booking.id
    ).order_by(RoomTransfer.transfer_time.desc()).all()
    
    return render_template('room_transfer/transfer_history.html',
                         booking=booking, transfers=transfers)

@room_transfer_bp.route('/test')
@login_required
def test_room_transfer():
    """صفحة اختبار نقل الغرف"""
    # الحصول على الحجوزات النشطة
    active_bookings = Booking.query.filter_by(status='checked_in').all()

    # إحصائيات
    active_bookings_count = len(active_bookings)
    available_rooms_count = Room.query.filter_by(status='available').count()

    return render_template('test_room_transfer.html',
                         title='اختبار نقل الغرف',
                         active_bookings=active_bookings,
                         active_bookings_count=active_bookings_count,
                         available_rooms_count=available_rooms_count)
