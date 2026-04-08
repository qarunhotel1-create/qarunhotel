from datetime import datetime
from hotel import db
from hotel.utils.datetime_utils import get_egypt_now_naive

# Payment types
PAYMENT_TYPE_CASH = 'cash'
PAYMENT_TYPE_CARD = 'card'
PAYMENT_TYPE_BANK_TRANSFER = 'bank_transfer'

# Payment status
PAYMENT_STATUS_PENDING = 'pending'
PAYMENT_STATUS_COMPLETED = 'completed'
PAYMENT_STATUS_CANCELLED = 'cancelled'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # المستخدم الذي أضاف الدفعة
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False, default=PAYMENT_TYPE_CASH)
    payment_date = db.Column(db.DateTime, default=get_egypt_now_naive)
    status = db.Column(db.String(20), default=PAYMENT_STATUS_COMPLETED)
    notes = db.Column(db.Text)
    attachment_file = db.Column(db.String(255))  # مسار الملف المرفق للتحويل البنكي
    created_at = db.Column(db.DateTime, default=get_egypt_now_naive)

    # العلاقات
    user = db.relationship('User', backref='payments')
    
    def __init__(self, booking_id, amount, payment_type=PAYMENT_TYPE_CASH, notes=None, attachment_file=None, user_id=None):
        self.booking_id = booking_id
        self.amount = amount
        self.payment_type = payment_type
        self.notes = notes
        self.attachment_file = attachment_file
        self.user_id = user_id
        self.status = PAYMENT_STATUS_COMPLETED
    
    @property
    def has_attachment(self):
        """التحقق من وجود ملف مرفق"""
        return self.attachment_file is not None and self.attachment_file.strip() != ''

    @property
    def attachment_file_extension(self):
        """الحصول على امتداد الملف المرفق"""
        if self.has_attachment:
            return self.attachment_file.split('.')[-1].lower()
        return None

    @property
    def is_image_attachment(self):
        """التحقق من كون الملف المرفق صورة"""
        if self.attachment_file_extension:
            return self.attachment_file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return False

    @property
    def is_pdf_attachment(self):
        """التحقق من كون الملف المرفق PDF"""
        return self.attachment_file_extension == 'pdf'

    def __repr__(self):
        return f'<Payment {self.id}: {self.amount} جنيه>'
