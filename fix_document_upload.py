# -*- coding: utf-8 -*-
"""
هذا الملف يقوم بإصلاح مشاكل رفع الوثائق في نظام الفندق
يعالج مشاكل الترميز وأسماء الملفات وحفظ البيانات الفارغة
"""

import os
import sys
import re
import unicodedata
import shutil
from datetime import datetime

# تأكد من تضمين مسار المشروع
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# استيراد المكتبات اللازمة من المشروع
try:
    from hotel import create_app, db
    from hotel.models.document import CustomerDocument
    print("✅ تم استيراد المكتبات بنجاح")
except Exception as e:
    print(f"❌ خطأ في استيراد المكتبات: {str(e)}")
    sys.exit(1)

# إنشاء تطبيق فلاسك
app = create_app()

# تعريف المسارات
UPLOAD_FOLDER = os.path.join('hotel', 'static', 'uploads', 'customers')
BACKUP_FOLDER = os.path.join('hotel', 'static', 'uploads', 'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))

# دالة لتنظيف اسم الملف
def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المدعومة"""
    # إزالة الأحرف غير المرئية والتحكم
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # تنظيف شامل لاسم الملف
    clean_name = filename.strip()
    
    # استبدال جميع الأحرف الخاصة والمسافات
    clean_name = re.sub(r'[^\w\-_.]', '_', clean_name)
    
    # تقليل الشرطات السفلية المتعددة
    clean_name = re.sub(r'_+', '_', clean_name)
    
    # إزالة الشرطات من البداية والنهاية
    clean_name = clean_name.strip('_')
    
    # التأكد من وجود اسم ملف صالح
    if not clean_name or clean_name == '':
        clean_name = 'document'
    
    return clean_name

# دالة لإصلاح ترميز الملفات
def fix_file_encoding(file_path):
    """إصلاح ترميز الملفات"""
    try:
        # قراءة الملف بترميز UTF-8
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # إعادة كتابة الملف بترميز UTF-8 مع BOM
        with open(file_path, 'wb') as f:
            # إضافة BOM للملفات النصية فقط
            if file_path.endswith(('.txt', '.html', '.css', '.js')):
                f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write(content)
        
        return True
    except Exception as e:
        print(f"❌ خطأ في إصلاح ترميز الملف {file_path}: {str(e)}")
        return False

# دالة لإنشاء نسخة احتياطية من مجلد الرفع
def create_backup():
    """إنشاء نسخة احتياطية من مجلد الرفع"""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            print(f"⚠️ مجلد الرفع غير موجود: {UPLOAD_FOLDER}")
            return False
        
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)
        
        # نسخ جميع الملفات
        for filename in os.listdir(UPLOAD_FOLDER):
            src_path = os.path.join(UPLOAD_FOLDER, filename)
            dst_path = os.path.join(BACKUP_FOLDER, filename)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
        
        print(f"✅ تم إنشاء نسخة احتياطية في: {BACKUP_FOLDER}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء النسخة الاحتياطية: {str(e)}")
        return False

# دالة لإصلاح أسماء الملفات في قاعدة البيانات
def fix_database_filenames():
    """إصلاح أسماء الملفات في قاعدة البيانات"""
    with app.app_context():
        try:
            # الحصول على جميع الوثائق
            documents = CustomerDocument.query.all()
            print(f"ℹ️ عدد الوثائق في قاعدة البيانات: {len(documents)}")
            
            fixed_count = 0
            for doc in documents:
                # تنظيف اسم الملف الأصلي
                if doc.original_name:
                    clean_name = clean_filename(doc.original_name)
                    if clean_name != doc.original_name:
                        doc.original_name = clean_name
                        fixed_count += 1
                        print(f"✅ تم إصلاح اسم الملف الأصلي: {doc.id} - {clean_name}")
            
            # حفظ التغييرات
            if fixed_count > 0:
                db.session.commit()
                print(f"✅ تم إصلاح {fixed_count} اسم ملف في قاعدة البيانات")
            else:
                print("ℹ️ لم يتم العثور على أسماء ملفات تحتاج إلى إصلاح")
            
            return fixed_count
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في إصلاح أسماء الملفات في قاعدة البيانات: {str(e)}")
            return -1

# دالة لإصلاح ملفات الوثائق
def fix_document_files():
    """إصلاح ملفات الوثائق"""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            print(f"✅ تم إنشاء مجلد الرفع: {UPLOAD_FOLDER}")
        
        # إصلاح ترميز جميع الملفات
        fixed_count = 0
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                if fix_file_encoding(file_path):
                    fixed_count += 1
        
        print(f"✅ تم إصلاح ترميز {fixed_count} ملف")
        return fixed_count
    except Exception as e:
        print(f"❌ خطأ في إصلاح ملفات الوثائق: {str(e)}")
        return -1

# دالة لإنشاء ملف تكوين الترميز
def create_encoding_config():
    """إنشاء ملف تكوين الترميز"""
    config_path = os.path.join('hotel', 'encoding_config.py')
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("""# -*- coding: utf-8 -*-
"""
تكوين الترميز للتطبيق
"""

# تكوين الترميز الافتراضي
DEFAULT_ENCODING = 'utf-8'

# تكوين ترميز الملفات
FILE_ENCODING = 'utf-8'

# تكوين ترميز قاعدة البيانات
DATABASE_ENCODING = 'utf-8'

# دالة لتنظيف اسم الملف
def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المدعومة"""
    import re
    import unicodedata
    
    # إزالة الأحرف غير المرئية والتحكم
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # تنظيف شامل لاسم الملف
    clean_name = filename.strip()
    
    # استبدال جميع الأحرف الخاصة والمسافات
    clean_name = re.sub(r'[^\\w\\-_.]', '_', clean_name)
    
    # تقليل الشرطات السفلية المتعددة
    clean_name = re.sub(r'_+', '_', clean_name)
    
    # إزالة الشرطات من البداية والنهاية
    clean_name = clean_name.strip('_')
    
    # التأكد من وجود اسم ملف صالح
    if not clean_name or clean_name == '':
        clean_name = 'document'
    
    return clean_name
""")
        print(f"✅ تم إنشاء ملف تكوين الترميز: {config_path}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء ملف تكوين الترميز: {str(e)}")
        return False

# دالة لتعديل ملف save_document_from_data
def patch_save_document_function():
    """تعديل دالة حفظ الوثائق لمعالجة مشاكل الترميز"""
    patch_path = os.path.join('hotel', 'routes', 'document_save_patch.py')
    try:
        with open(patch_path, 'w', encoding='utf-8') as f:
            f.write("""# -*- coding: utf-8 -*-
"""
تصحيح لدالة حفظ الوثائق
"""

import os
import base64
import re
import unicodedata
from werkzeug.utils import secure_filename
from flask import current_app, flash
from hotel.models.document import CustomerDocument
from hotel import db

# تعريف المسارات
UPLOAD_FOLDER = os.path.join('hotel', 'static', 'uploads', 'customers')

# دالة لتنظيف اسم الملف
def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المدعومة"""
    # إزالة الأحرف غير المرئية والتحكم
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # تنظيف شامل لاسم الملف
    clean_name = filename.strip()
    
    # استبدال جميع الأحرف الخاصة والمسافات
    clean_name = re.sub(r'[^\\w\\-_.]', '_', clean_name)
    
    # تقليل الشرطات السفلية المتعددة
    clean_name = re.sub(r'_+', '_', clean_name)
    
    # إزالة الشرطات من البداية والنهاية
    clean_name = clean_name.strip('_')
    
    # التأكد من وجود اسم ملف صالح
    if not clean_name or clean_name == '':
        clean_name = 'document'
    
    return clean_name

# دالة لإنشاء مجلد الرفع
def create_upload_folder():
    """إنشاء مجلد الرفع إذا لم يكن موجوداً"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"تم إنشاء مجلد الرفع: {UPLOAD_FOLDER}")
    return UPLOAD_FOLDER

# دالة محسنة لحفظ الوثيقة من البيانات
def enhanced_save_document_from_data(customer, doc_data):
    """نسخة محسنة من دالة حفظ الوثيقة من البيانات"""
    print("بدء enhanced_save_document_from_data")
    
    # التأكد من وجود مجلد الرفع
    create_upload_folder()
    
    # معالجة شاملة للأخطاء مع تفاصيل كاملة
    try:
        # التحقق من صحة البيانات الأساسية
        if not doc_data:
            print("doc_data فارغ")
            return None
            
        if not isinstance(doc_data, dict):
            print(f"doc_data ليس dictionary: {type(doc_data)}")
            return None
        
        # استخراج البيانات مع قيم افتراضية آمنة
        data_url = doc_data.get('data', '')
        filename = doc_data.get('name', 'document.file')
        file_size = doc_data.get('size', 0)
        mime_type = doc_data.get('type', 'application/octet-stream')
        
        print(f"البيانات المستخرجة:")
        print(f"  - اسم الملف: '{filename}'")
        print(f"  - الحجم: {file_size}")
        print(f"  - النوع: '{mime_type}'")
        print(f"  - طول data_url: {len(data_url) if data_url else 0}")
        
        # التحقق من البيانات الأساسية
        if not data_url:
            print("data_url فارغ")
            flash('فشل حفظ الوثيقة: البيانات المرسلة من المتصفح فارغة. حاول إعادة رفع الملف.', 'danger')
            return None
        
        # معالجة اسم الملف بشكل آمن
        clean_name = clean_filename(filename)
        if not clean_name or clean_name == '':
            clean_name = 'document'
        
        # التأكد من وجود امتداد
        if '.' not in clean_name:
            if mime_type.startswith('image/'):
                if 'jpeg' in mime_type or 'jpg' in mime_type:
                    clean_name += '.jpg'
                elif 'png' in mime_type:
                    clean_name += '.png'
                else:
                    clean_name += '.jpg'
            elif mime_type == 'application/pdf':
                clean_name += '.pdf'
            else:
                clean_name += '.file'
        
        print(f"اسم الملف بعد التنظيف: '{clean_name}'")
        
        # فك تشفير base64 مع معالجة شاملة
        try:
            if not data_url.startswith('data:'):
                print("تنسيق البيانات غير صحيح (لا تبدأ بـ 'data:')")
                flash('فشل حفظ الوثيقة: تنسيق البيانات غير صحيح.', 'danger')
                return None
            
            # تقسيم البيانات
            if ',' not in data_url:
                print("تنسيق data_url غير صحيح (لا يحتوي على فاصلة)")
                flash('فشل حفظ الوثيقة: البيانات المرسلة غير مكتملة.', 'danger')
                return None
                
            header, encoded = data_url.split(',', 1)
            
            if not encoded or encoded.strip() == '':
                print("البيانات المشفرة فارغة")
                flash('فشل حفظ الوثيقة: البيانات المشفرة فارغة.', 'danger')
                return None
            
            # فك التشفير
            try:
                file_bytes = base64.b64decode(encoded)
            except Exception as decode_error:
                print(f"خطأ في فك تشفير base64: {str(decode_error)}")
                # محاولة إصلاح البيانات المشفرة
                encoded = encoded.replace(' ', '+')  # استبدال المسافات بعلامات +
                try:
                    file_bytes = base64.b64decode(encoded)
                    print("تم إصلاح البيانات المشفرة ونجح فك التشفير")
                except Exception as retry_error:
                    print(f"فشل في إصلاح البيانات المشفرة: {str(retry_error)}")
                    flash('فشل حفظ الوثيقة: خطأ في فك تشفير البيانات.', 'danger')
                    return None
            
            print(f"تم فك تشفير {len(file_bytes)} بايت من base64")
            
            if len(file_bytes) == 0:
                print("الملف فارغ بعد فك التشفير")
                flash('فشل حفظ الوثيقة: الملف فارغ بعد فك التشفير.', 'danger')
                return None
                
        except Exception as e:
            print(f"خطأ في فك التشفير base64: {str(e)}")
            current_app.logger.error(f'Error decoding base64 data for file {clean_name}: {str(e)}', exc_info=True)
            flash(f'فشل حفظ الوثيقة: خطأ في فك التشفير.', 'danger')
            return None
        
        # إنشاء مسار الملف مع معالجة آمنة
        try:
            original_filename = secure_filename(clean_name)
            if not original_filename:
                original_filename = 'document.file'
                
            unique_filename = CustomerDocument.generate_filename(original_filename)
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            print(f"المسار الفريد للملف: {file_path}")
            
        except Exception as e:
            print(f"خطأ في إنشاء مسار الملف: {str(e)}")
            flash(f'فشل حفظ الوثيقة: خطأ في إنشاء مسار الملف.', 'danger')
            return None
        
        # حفظ الملف
        try:
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            print(f"تم حفظ الملف في: {file_path}")
        except Exception as e:
            print(f"خطأ في حفظ الملف على القرص: {str(e)}")
            current_app.logger.error(f'Error writing file to disk: {str(e)}', exc_info=True)
            
            # محاولة إنشاء المجلد مرة أخرى
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(file_bytes)
                print(f"تم حفظ الملف في المحاولة الثانية: {file_path}")
            except Exception as retry_error:
                print(f"فشل في المحاولة الثانية لحفظ الملف: {str(retry_error)}")
                flash(f'فشل حفظ الوثيقة: خطأ في كتابة الملف على القرص.', 'danger')
                return None
        
        # التحقق من حفظ الملف
        if not os.path.exists(file_path):
            print(f"الملف غير موجود بعد الحفظ: {file_path}")
            flash('فشل حفظ الوثيقة: الملف غير موجود بعد الحفظ.', 'danger')
            return None
        
        actual_size = os.path.getsize(file_path)
        if actual_size == 0:
            print(f"الملف فارغ بعد الحفظ: {file_path}")
            flash('فشل حفظ الوثيقة: الملف فارغ بعد الحفظ.', 'danger')
            os.remove(file_path)
            return None
        
        print(f"تم التحقق من الملف بنجاح: {actual_size} بايت")
        
        # إنشاء سجل الوثيقة
        document = CustomerDocument(
            customer_id=customer.id,
            filename=unique_filename,
            original_name=original_filename,
            file_type=CustomerDocument.get_file_type(mime_type),
            file_extension=original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else '',
            file_size=len(file_bytes),
            mime_type=mime_type,
            scan_method='upload',
            is_scanned=False,
            status='active'
        )
        print(f"تم إنشاء سجل الوثيقة لـ: {document.original_name}")
        
        db.session.add(document)
        print("تم إضافة الوثيقة إلى الجلسة.")
        return document
        
    except Exception as e:
        print(f"خطأ عام في enhanced_save_document_from_data: {str(e)}")
        current_app.logger.error(f'Error saving document from data: {str(e)}', exc_info=True)
        
        # محاولة طارئة للحفظ
        try:
            import time
            emergency_filename = f"emergency_file_{int(time.time())}.jpg"
            
            data_url = doc_data.get('data', '') if doc_data else ''
            if data_url and ',' in data_url:
                header, encoded = data_url.split(',', 1)
                file_bytes = base64.b64decode(encoded)
                
                if len(file_bytes) > 0:
                    unique_filename = f"emrg_{int(time.time())}_{len(file_bytes)}.jpg"
                    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(file_bytes)
                    
                    # إنشاء سجل بسيط
                    document = CustomerDocument(
                        customer_id=customer.id,
                        filename=unique_filename,
                        original_name=emergency_filename,
                        file_type='image',
                        file_extension='jpg',
                        file_size=len(file_bytes),
                        mime_type='image/jpeg',
                        scan_method='upload',
                        is_scanned=False,
                        status='active'
                    )
                    
                    db.session.add(document)
                    print(f"تم حفظ الملف بالطريقة الطارئة: {emergency_filename}")
                    return document
                    
        except Exception as emergency_error:
            print(f"فشلت المحاولة الطارئة: {str(emergency_error)}")
        
        return None
""")
        print(f"✅ تم إنشاء ملف تصحيح دالة حفظ الوثائق: {patch_path}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء ملف تصحيح دالة حفظ الوثائق: {str(e)}")
        return False

# دالة رئيسية
def main():
    """الدالة الرئيسية للبرنامج"""
    print("="*50)
    print("🔧 برنامج إصلاح مشاكل رفع الوثائق")
    print("="*50)
    
    # إنشاء نسخة احتياطية
    create_backup()
    
    # إصلاح ملفات الوثائق
    fix_document_files()
    
    # إصلاح أسماء الملفات في قاعدة البيانات
    fix_database_filenames()
    
    # إنشاء ملف تكوين الترميز
    create_encoding_config()
    
    # تعديل دالة حفظ الوثائق
    patch_save_document_function()
    
    print("\n" + "="*50)
    print("✅ تم الانتهاء من إصلاح مشاكل رفع الوثائق")
    print("="*50)
    print("\nلتطبيق الإصلاحات، قم بالخطوات التالية:")
    print("1. انسخ ملف encoding_config.py إلى مجلد hotel")
    print("2. استورد الدالة enhanced_save_document_from_data من document_save_patch.py")
    print("3. استبدل دالة save_document_from_data بالدالة enhanced_save_document_from_data")
    print("="*50)

# تشغيل البرنامج
if __name__ == "__main__":
    main()