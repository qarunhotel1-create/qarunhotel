from hotel import db
from datetime import datetime
from hotel.utils.datetime_utils import get_egypt_now_naive
import os
import uuid


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(20), unique=True, nullable=True)
    nationality = db.Column(db.String(50))
    marital_status = db.Column(db.String(20))
    gender = db.Column(db.String(10))  # حقل الجنس (ذكر/أنثى)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    # حقل الملاحظات
    notes = db.Column(db.Text)
    
    # حقول الحظر
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    block_reason = db.Column(db.String(500))
    blocked_at = db.Column(db.DateTime)
    blocked_by = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=get_egypt_now_naive)
    updated_at = db.Column(db.DateTime, default=get_egypt_now_naive, onupdate=get_egypt_now_naive)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))



    # العلاقات
    bookings = db.relationship('Booking', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('CustomerDocument', backref='customer', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(Customer, self).__init__(**kwargs)
        self.created_at = get_egypt_now_naive()
        self.updated_at = get_egypt_now_naive()

    @property
    def full_name(self):
        return self.name

    @property
    def has_documents(self):
        """التحقق من وجود وثائق مرفقة نشطة"""
        return self.documents.filter_by(status='active').count() > 0

    @property
    def documents_count(self):
        """عدد الوثائق المرفقة النشطة"""
        return self.documents.filter_by(status='active').count()

    @property
    def active_documents(self):
        """الحصول على الوثائق النشطة فقط"""
        return self.documents.filter_by(status='active').all()

    @property
    def scanned_documents_count(self):
        """عدد الوثائق الممسوحة ضوئياً"""
        return self.documents.filter_by(status='active', is_scanned=True).count()

    @property
    def uploaded_documents_count(self):
        """عدد الوثائق المرفوعة"""
        return self.documents.filter_by(status='active', is_scanned=False).count()

    def get_documents_by_scan_method(self, scan_method):
        """الحصول على الوثائق حسب طريقة الإضافة"""
        return self.documents.filter_by(status='active', scan_method=scan_method).all()
    
    def block_customer(self, reason, blocked_by_user):
        """حظر العميل"""
        try:
            self.is_blocked = True
            self.block_reason = reason
            self.blocked_at = get_egypt_now_naive()
            self.blocked_by = blocked_by_user
            self.updated_at = get_egypt_now_naive()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في حظر العميل: {e}")
            return False
    
    def unblock_customer(self):
        """إلغاء حظر العميل"""
        try:
            self.is_blocked = False
            self.block_reason = None
            self.blocked_at = None
            self.blocked_by = None
            self.updated_at = get_egypt_now_naive()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في إلغاء حظر العميل: {e}")
            return False
    
    @property
    def block_status_text(self):
        """نص حالة الحظر"""
        if self.is_blocked:
            return f"محظور - {self.block_reason}"
        return "نشط"
    
    @property
    def can_make_booking(self):
        """هل يمكن للعميل عمل حجز"""
        return not self.is_blocked

    def delete_all_documents(self, soft_delete=True):
        """حذف جميع الوثائق (حذف ناعم أو صلب)"""
        for document in self.documents.filter_by(status='active'):
            if soft_delete:
                document.soft_delete()
            else:
                document.delete_file()
                db.session.delete(document)
        if not soft_delete:
            db.session.commit()

    def __repr__(self):
        try:
            # معالجة آمنة للنصوص العربية في __repr__
            safe_name = self.name[:20] if self.name else "No Name"
            safe_id = self.id_number[:10] if self.id_number else "No ID"
            return f'<Customer {safe_name} - {safe_id}>'
        except Exception:
            return f'<Customer ID:{self.id}>'
