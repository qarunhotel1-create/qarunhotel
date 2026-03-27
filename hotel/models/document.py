from hotel import db
from datetime import datetime
from hotel.utils.datetime_utils import get_egypt_now_naive
import os
import uuid


class CustomerDocument(db.Model):
    """نموذج وثائق العملاء الجديد - يدعم رفع متعدد وماسح ضوئي متقدم"""
    __tablename__ = 'customer_documents'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # معلومات الملف
    filename = db.Column(db.String(255), nullable=False)  # اسم الملف المخزن
    original_name = db.Column(db.String(255), nullable=False)  # الاسم الأصلي
    file_type = db.Column(db.String(50), nullable=False)  # نوع الملف (image, pdf, document)
    file_extension = db.Column(db.String(10), nullable=False)  # امتداد الملف
    file_size = db.Column(db.Integer, nullable=False)  # حجم الملف بالبايت
    mime_type = db.Column(db.String(100), nullable=False)  # نوع MIME
    
    # معلومات الوثيقة
    document_title = db.Column(db.String(200))  # عنوان الوثيقة
    description = db.Column(db.Text)  # وصف الوثيقة
    
    # معلومات المسح الضوئي الجديدة
    is_scanned = db.Column(db.Boolean, default=False)  # هل هي ممسوحة ضوئياً
    scan_method = db.Column(db.String(50), default='upload')  # طريقة الإضافة (upload, scan)
    pages_count = db.Column(db.Integer, default=1)  # عدد الصفحات
    scan_quality = db.Column(db.String(20), default='high')  # جودة المسح
    scan_resolution = db.Column(db.Integer, default=300)  # دقة المسح
    
    # حالة الوثيقة
    status = db.Column(db.String(20), default='active')  # active, deleted, archived
    is_verified = db.Column(db.Boolean, default=False)  # هل تم التحقق من الوثيقة
    
    # تواريخ
    upload_date = db.Column(db.DateTime, default=get_egypt_now_naive)
    created_at = db.Column(db.DateTime, default=get_egypt_now_naive)
    updated_at = db.Column(db.DateTime, default=get_egypt_now_naive, onupdate=get_egypt_now_naive)
    
    # العلاقات
    # العلاقة معرفة في نموذج العميل

    def __init__(self, **kwargs):
        super(CustomerDocument, self).__init__(**kwargs)
        self.created_at = get_egypt_now_naive()
        self.updated_at = get_egypt_now_naive()

    @property
    def file_url(self):
        """الحصول على رابط الملف"""
        return f'/static/uploads/customers/{self.filename}'

    @property
    def file_size_formatted(self):
        """تنسيق حجم الملف"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def is_image(self):
        """التحقق من كون الملف صورة"""
        return self.file_type == 'image'

    @property
    def is_pdf(self):
        """التحقق من كون الملف PDF"""
        return self.file_type == 'pdf'

    @property
    def is_document(self):
        """التحقق من كون الملف مستند"""
        return self.file_type == 'document'
    
    @property
    def is_video(self):
        """التحقق من كون الملف فيديو"""
        return self.file_type == 'video'
    
    @property
    def is_audio(self):
        """التحقق من كون الملف صوتي"""
        return self.file_type == 'audio'
    
    @property
    def is_archive(self):
        """التحقق من كون الملف أرشيف"""
        return self.file_type == 'archive'

    @property
    def icon_class(self):
        """الحصول على أيقونة الملف - محسن لدعم أنواع أكثر"""
        icons = {
            'image': 'fas fa-file-image text-success',
            'pdf': 'fas fa-file-pdf text-danger',
            'document': 'fas fa-file-word text-primary',
            'video': 'fas fa-file-video text-warning',
            'audio': 'fas fa-file-audio text-info',
            'archive': 'fas fa-file-archive text-secondary',
            'other': 'fas fa-file text-muted'
        }
        return icons.get(self.file_type, icons['other'])

    @property
    def scan_method_display(self):
        """عرض طريقة الإضافة بالعربية"""
        methods = {
            'upload': 'رفع ملف',
            'scan': 'مسح ضوئي',
            'multi_scan': 'مسح متعدد الصفحات'
        }
        return methods.get(self.scan_method, 'غير محدد')

    @staticmethod
    def generate_filename(original_filename):
        """توليد اسم ملف فريد"""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        filename = f"doc_{uuid.uuid4().hex}.{ext}" if ext else f"doc_{uuid.uuid4().hex}"
        return filename

    @staticmethod
    def get_file_type(mime_type):
        """تحديد نوع الملف من MIME type - محسن لدعم أنواع أكثر"""
        if not mime_type:
            return 'other'
            
        mime_type = mime_type.lower()
        
        if mime_type.startswith('image/'):
            return 'image'
        elif 'pdf' in mime_type:
            return 'pdf'
        elif any(doc_type in mime_type for doc_type in ['word', 'document', 'text', 'rtf', 'excel', 'sheet', 'powerpoint', 'presentation']):
            return 'document'
        elif any(video_type in mime_type for video_type in ['video/', 'mp4', 'avi', 'mov', 'wmv']):
            return 'video'
        elif any(audio_type in mime_type for audio_type in ['audio/', 'mp3', 'wav', 'ogg']):
            return 'audio'
        elif any(archive_type in mime_type for archive_type in ['zip', 'rar', '7z', 'tar', 'gz']):
            return 'archive'
        else:
            return 'other'

    @staticmethod
    def is_allowed_file(filename, mime_type):
        """التحقق من أن الملف مسموح - يقبل جميع أنواع الملفات بدون قيود"""
        # إزالة جميع القيود - يقبل أي نوع ملف
        return True

    def delete_file(self):
        """حذف الملف من القرص"""
        try:
            filepath = os.path.join('hotel', 'static', 'uploads', 'customers', self.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False

    def soft_delete(self):
        """حذف ناعم للوثيقة مع حذف الملف من القرص"""
        # حذف الملف فعلياً (يتم تجاهل أي أخطاء داخل delete_file)
        self.delete_file()
        self.status = 'deleted'
        self.updated_at = get_egypt_now_naive()
        db.session.commit()

    def restore(self):
        """استعادة الوثيقة المحذوفة"""
        self.status = 'active'
        self.updated_at = get_egypt_now_naive()
        db.session.commit()

    def verify(self):
        """تأكيد الوثيقة"""
        self.is_verified = True
        self.updated_at = get_egypt_now_naive()
        db.session.commit()

    def __repr__(self):
        return f'<CustomerDocument {self.original_name} for Customer {self.customer_id}>'