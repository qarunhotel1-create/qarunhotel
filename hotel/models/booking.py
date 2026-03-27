from datetime import datetime
from hotel import db
from hotel.utils.datetime_utils import get_egypt_now_naive

# Booking status
BOOKING_STATUS_PENDING = 'pending'
BOOKING_STATUS_CONFIRMED = 'confirmed'
BOOKING_STATUS_CHECKED_IN = 'checked_in'
BOOKING_STATUS_CHECKED_OUT = 'checked_out'
BOOKING_STATUS_CANCELLED = 'cancelled'

class Booking(db.Model):
    __tablename__ = 'bookings'
    # Use unique index created via migration for SQLite instead of SQL-level UniqueConstraint
    __table_args__ = ()
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default=BOOKING_STATUS_PENDING)

    # معلومات السعر والخصم
    occupancy_type = db.Column(db.String(20), default='single')  # نوع الإقامة
    is_deus = db.Column(db.Boolean, default=False)  # نوع الحساب (ديوز أم عادي)
    base_price = db.Column(db.Float)  # السعر الأساسي قبل الخصم
    discount_percentage = db.Column(db.Float, default=0.0)  # نسبة الخصم المئوية
    discount_amount = db.Column(db.Float, default=0.0)  # مبلغ الخصم بالجنيه (جديد)
    tax_percentage = db.Column(db.Float, default=0.0)  # نسبة الضريبة المئوية
    tax_amount = db.Column(db.Float, default=0.0)  # مبلغ الضريبة
    total_price = db.Column(db.Float)  # السعر النهائي بعد الخصم والضريبة
    paid_amount = db.Column(db.Float, default=0.0)

    # معلومات الديوز (6 ساعات)
    deus_start_time = db.Column(db.DateTime)  # وقت بداية الديوز (عند تسجيل الدخول)
    deus_end_time = db.Column(db.DateTime)  # وقت نهاية الديوز (بعد 6 ساعات)
    deus_expired = db.Column(db.Boolean, default=False)  # هل انتهت فترة الديوز

    # أوقات تسجيل الدخول والخروج
    check_in_time = db.Column(db.DateTime)  # وقت تسجيل الدخول الفعلي
    check_out_time = db.Column(db.DateTime)  # وقت تسجيل الخروج الفعلي

    created_at = db.Column(db.DateTime, default=get_egypt_now_naive)
    notes = db.Column(db.Text)

    # ترقيم سنوي
    booking_year = db.Column(db.Integer, index=True)  # سنة الحجز
    year_seq = db.Column(db.Integer)                 # الرقم التسلسلي داخل السنة

    # Relationships
    payments = db.relationship('Payment', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, user_id, room_id, customer_id, check_in_date, check_out_date,
                 occupancy_type='single', is_deus=False, base_price=None, discount_percentage=0.0,
                 tax_percentage=0.0, tax_amount=0.0, total_price=None, paid_amount=0.0, notes=None):
        self.user_id = user_id
        self.room_id = room_id
        self.customer_id = customer_id
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.occupancy_type = occupancy_type
        self.is_deus = is_deus
        self.base_price = base_price
        self.discount_percentage = discount_percentage
        self.tax_percentage = tax_percentage
        self.tax_amount = tax_amount
        self.total_price = total_price
        self.paid_amount = paid_amount
        self.notes = notes
        self.status = BOOKING_STATUS_PENDING
    
    @property
    def booking_code(self) -> str:
        """إرجاع الكود بصيغة YYYY/NN إن توفّر، وإلا يرجع معرف السجل."""
        if self.booking_year and self.year_seq:
            return f"{self.booking_year}/{self.year_seq}"
        return str(self.id) if self.id is not None else ''

    @classmethod
    def next_sequence_for_year(cls, year: int) -> int:
        """إيجاد آخر رقم تسلسلي لتلك السنة ثم زيادته بواحد."""
        from sqlalchemy import func
        max_seq = db.session.query(func.max(cls.year_seq)).filter(cls.booking_year == year).scalar()
        return 1 if not max_seq else int(max_seq) + 1

    def is_active(self):
        return self.status in [BOOKING_STATUS_PENDING, BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_CHECKED_IN]

    @property
    def remaining_amount(self):
        """حساب المبلغ المتبقي"""
        return (self.total_price or 0) - (self.paid_amount or 0)

    @property
    def is_fully_paid(self):
        """التحقق من اكتمال الدفع"""
        return self.remaining_amount <= 0

    @property
    def payment_percentage(self):
        """حساب نسبة الدفع"""
        if not self.total_price or self.total_price == 0:
            return 0
        return min(100, (self.paid_amount or 0) / self.total_price * 100)

    @property
    def account_type_display(self):
        """عرض نوع الحساب"""
        return 'ديوز' if self.is_deus else 'عادي'

    @property
    def occupancy_type_display(self):
        """عرض نوع الحجز"""
        occupancy_types = {
            'single': 'Single - إقامة مفردة',
            'double': 'Double - إقامة مزدوجة',
            'triple': 'Triple - إقامة ثلاثية'
        }
        return occupancy_types.get(self.occupancy_type, self.occupancy_type)

    @property
    def deus_remaining_time(self):
        """حساب الوقت المتبقي للديوز بالدقائق"""
        if not self.is_deus or not self.deus_start_time or self.deus_expired:
            return 0

        from datetime import timedelta
        from hotel.utils.datetime_utils import get_egypt_now
        now = get_egypt_now()

        if not self.deus_end_time:
            # حساب وقت النهاية (6 ساعات من البداية)
            end_time = self.deus_start_time + timedelta(hours=6)
        else:
            end_time = self.deus_end_time

        if now >= end_time:
            return 0

        remaining = end_time - now
        return int(remaining.total_seconds() / 60)  # بالدقائق

    @property
    def deus_status_display(self):
        """عرض حالة الديوز"""
        if not self.is_deus:
            return 'غير ديوز'

        if not self.deus_start_time:
            return 'لم يبدأ'

        if self.deus_expired:
            return 'انتهى'

        remaining = self.deus_remaining_time
        if remaining <= 0:
            return 'انتهى'

        hours = remaining // 60
        minutes = remaining % 60
        return f'متبقي {hours}:{minutes:02d}'

    # @property
    # def discount_amount(self):
    #     """حساب مبلغ الخصم - يُطبق على الإجمالي شامل الضريبة"""
    #     if not self.base_price or not self.discount_percentage:
    #         return 0
    #     # حساب الإجمالي مع الضريبة أولاً
    #     total_with_tax = self.base_price + (self.tax_amount or 0)
    #     # تطبيق الخصم على الإجمالي
    #     return (total_with_tax * self.discount_percentage) / 100

    @property
    def calculated_discount_amount(self):
        """حساب مبلغ الخصم المئوي ديناميكياً (للعرض فقط)"""
        if not self.base_price or not self.discount_percentage:
            return 0
        total_with_tax = self.base_price + (self.tax_amount or 0)
        return (total_with_tax * self.discount_percentage) / 100

    def calculate_total_with_discount(self):
        """حساب السعر النهائي مع الخصم"""
        if not self.base_price:
            return 0
        # حساب الإجمالي مع الضريبة
        total_with_tax = self.base_price + (self.tax_amount or 0)
        # تطبيق الخصم
        discount_amount = self.discount_amount
        return total_with_tax - discount_amount

    def update_paid_amount(self):
        """تحديث المبلغ المدفوع من مجموع الدفعات"""
        total_paid = sum(payment.amount for payment in self.payments if payment.status == 'completed')
        self.paid_amount = total_paid

    def get_status_display(self):
        """عرض حالة الحجز بالعربية"""
        status_map = {
            'pending': 'قيد الانتظار',
            'confirmed': 'مؤكدة',
            'checked_in': 'نشطة',
            'checked_out': 'مكتملة',
            'cancelled': 'ملغاة'
        }
        return status_map.get(self.status, self.status)

    def get_status_color(self):
        """إرجاع لون Bootstrap للحالة"""
        color_map = {
            'pending': 'warning',
            'confirmed': 'info',
            'checked_in': 'success',
            'checked_out': 'secondary',
            'cancelled': 'danger'
        }
        return color_map.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Booking {self.id}>'
