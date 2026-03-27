from datetime import datetime
from hotel import db
from hotel.utils.datetime_utils import get_egypt_now_naive

class BookingGuest(db.Model):
    """نموذج المرافقين في الحجز"""
    __tablename__ = 'booking_guests'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    guest_type = db.Column(db.String(20), default='companion')  # companion, family, friend
    relationship = db.Column(db.String(100))  # العلاقة مع العميل الأساسي
    notes = db.Column(db.Text)  # ملاحظات إضافية
    is_primary = db.Column(db.Boolean, default=False)  # العميل الأساسي
    is_active = db.Column(db.Boolean, default=True)
    
    # معلومات الإضافة
    added_date = db.Column(db.DateTime, nullable=False, default=get_egypt_now_naive)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    added_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    added_time = db.Column(db.DateTime, default=get_egypt_now_naive)
    
    # معلومات الإزالة
    removed_date = db.Column(db.DateTime)
    removed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    removed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    removed_time = db.Column(db.DateTime, nullable=True)
    
    # العلاقات
    booking = db.relationship('Booking', backref=db.backref('guests', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('guest_bookings', lazy=True))
    added_by_user = db.relationship('User', foreign_keys=[added_by_user_id], backref='added_guests')
    removed_by_user = db.relationship('User', foreign_keys=[removed_by_user_id], backref='removed_guests')
    
    def __init__(self, booking_id, customer_id, guest_type='companion',
                 added_by_user_id=None, is_primary=False, relationship=None, notes=None):
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.guest_type = guest_type
        self.relationship = relationship
        self.notes = notes
        self.added_by_user_id = added_by_user_id
        self.added_by = added_by_user_id  # نفس القيمة
        self.added_date = get_egypt_now_naive()  # الحقل المطلوب
        self.is_primary = is_primary
        self.is_active = True
        self.added_time = get_egypt_now_naive()
    
    @property
    def guest_type_display(self):
        """عرض نوع المرافق بالعربية"""
        types = {
            'companion': 'مرافق',
            'family': 'عائلة',
            'friend': 'صديق',
            'colleague': 'زميل',
            'other': 'آخر'
        }
        return types.get(self.guest_type, 'مرافق')
    
    @property
    def status_badge_class(self):
        """فئة CSS لحالة المرافق"""
        if self.is_primary:
            return 'bg-primary'
        elif self.is_active:
            return 'bg-success'
        else:
            return 'bg-secondary'
    
    @property
    def added_time_display(self):
        """عرض وقت الإضافة"""
        if self.added_time:
            return self.added_time.strftime('%Y-%m-%d %H:%M')
        return 'غير محدد'
    
    @property
    def removed_time_display(self):
        """عرض وقت الإزالة"""
        if self.removed_time:
            return self.removed_time.strftime('%Y-%m-%d %H:%M')
        return 'غير محدد'
    
    def __repr__(self):
        return f'<BookingGuest {self.customer.name} in Booking {self.booking_id}>'
