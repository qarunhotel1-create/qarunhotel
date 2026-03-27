from datetime import datetime
from hotel import db
from hotel.utils.datetime_utils import get_egypt_now_naive

class RoomTransfer(db.Model):
    __tablename__ = 'room_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    from_room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    to_room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    from_room_check_in = db.Column(db.DateTime, nullable=False, default=get_egypt_now_naive)
    from_room_check_out = db.Column(db.DateTime, nullable=False, default=get_egypt_now_naive)
    to_room_check_in = db.Column(db.DateTime, nullable=False, default=get_egypt_now_naive)
    transfer_date = db.Column(db.DateTime, nullable=False, default=get_egypt_now_naive)
    transfer_time = db.Column(db.DateTime, nullable=False, default=get_egypt_now_naive)
    transferred_by = db.Column(db.String(100), nullable=False, default='admin')
    transferred_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # العلاقات
    booking = db.relationship('Booking', backref='room_transfers')
    from_room = db.relationship('Room', foreign_keys=[from_room_id], backref='transfers_from')
    to_room = db.relationship('Room', foreign_keys=[to_room_id], backref='transfers_to')
    transferred_by_user = db.relationship('User', backref='room_transfers')
    
    @property
    def transfer_time_display(self):
        """عرض وقت النقل بالتنسيق العربي"""
        return self.transfer_time.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def from_room_duration(self):
        """المدة الفعلية التي قضاها في الغرفة السابقة كتوقيت delta"""
        start = self.from_room_check_in
        end = self.from_room_check_out
        if not start or not end:
            return None
        delta = end - start
        if delta.total_seconds() < 0:
            return None
        return delta

    @property
    def from_room_duration_display(self):
        """عرض مدة الإقامة في الغرفة السابقة بصيغة عربية مقروءة"""
        delta = self.from_room_duration
        if not delta:
            return 'لا يوجد'
        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        parts = []
        if days:
            parts.append(f'{days} يوم')
        if hours:
            parts.append(f'{hours} ساعة')
        # إذا لم يكن هناك أيام أو ساعات، نظهر الدقائق على الأقل
        if minutes or not parts:
            parts.append(f'{minutes} دقيقة')
        return '، '.join(parts)

    @property
    def transfer_reason(self):
        """توافق مع القالب: إعادة تسمية السبب المخزن في الحقل reason"""
        return self.reason
    
    def __repr__(self):
        return f'<RoomTransfer {self.id}: Booking {self.booking_id} from Room {self.from_room_id} to Room {self.to_room_id}>'
