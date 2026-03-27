# -*- coding: utf-8 -*-
"""
تصحيح لدالة حفظ الوثائق
"""

import os
import base64
import re
import time
import unicodedata
import tempfile
from werkzeug.utils import secure_filename
from flask import current_app, flash
from hotel.models.document import CustomerDocument
from hotel import db

# تعريف المسارات بمسار مطلق آمن نسبةً إلى هذا الملف
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.abspath(os.path.join(BASE_DIR, '..', 'static', 'uploads', 'customers'))

# دالة لتنظيف اسم الملف
def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المدعومة ومعالجة خطأ [Errno 22] Invalid argument"""
    if not filename:
        return f'document_{int(time.time())}'
        
    # إزالة الأحرف غير المرئية والتحكم
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # تنظيف شامل لاسم الملف
    clean_name = filename.strip()
    
    # استبدال الأحرف الخاصة المعروفة بأنها تسبب مشاكل في نظام الملفات
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '\t', '\n', '\r', '\0', '\b', '\f', '\v', '\a']
    for char in invalid_chars:
        clean_name = clean_name.replace(char, '_')
    
    # معالجة خاصة للأحرف العربية والأحرف الخاصة
    # استبدال أي حرف غير أبجدي رقمي أو عربي بشرطة سفلية
    clean_name = re.sub(r'[^\w\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\.-]', '_', clean_name)
    
    # استبدال المسافات بشرطة سفلية
    clean_name = clean_name.replace(' ', '_')
    
    # تقليل الشرطات السفلية المتعددة
    clean_name = re.sub(r'_+', '_', clean_name)
    
    # إزالة الشرطات من البداية والنهاية
    clean_name = clean_name.strip('_')
    
    # التأكد من وجود اسم ملف صالح
    if not clean_name or clean_name == '':
        clean_name = f'document_{int(time.time())}'
    
    # تحديد الطول الأقصى لاسم الملف (بدون الامتداد)
    max_length = 80  # تقليل الطول الأقصى لتجنب مشاكل المسارات الطويلة
    if '.' in clean_name:
        name_part, ext_part = clean_name.rsplit('.', 1)
        if len(name_part) > max_length:
            name_part = name_part[:max_length]
        clean_name = f"{name_part}.{ext_part}"
    elif len(clean_name) > max_length:
        clean_name = clean_name[:max_length]
    
    # إضافة طابع زمني للملف لضمان فريدية الاسم
    if '.' in clean_name:
        name_part, ext_part = clean_name.rsplit('.', 1)
        clean_name = f"{name_part}_{int(time.time())}.{ext_part}"
    else:
        clean_name = f"{clean_name}_{int(time.time())}"
    
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
        
        # استخراج البيانات مع قيم افتراضية آمنة (دعم كل من data و content)
        data_url = doc_data.get('data') or doc_data.get('content') or ''
        filename = doc_data.get('name') or doc_data.get('filename') or 'document.file'
        file_size = doc_data.get('size', 0)
        mime_type = doc_data.get('type') or 'application/octet-stream'

        # إذا لم يصل type، نحاول استخلاصه من رأس data URL
        if (not mime_type or mime_type == 'application/octet-stream') and isinstance(data_url, str) and data_url.startswith('data:') and ';' in data_url:
            try:
                mime_type = data_url.split(':', 1)[1].split(';', 1)[0]
            except Exception:
                pass
        
        print(f"البيانات المستخرجة:")
        print(f"  - اسم الملف: '{filename}'")
        print(f"  - الحجم: {file_size}")
        print(f"  - النوع: '{mime_type}'")
        print(f"  - طول data_url: {len(data_url) if data_url else 0}")
        
        # التحقق من البيانات الأساسية
        if not data_url:
            print("data_url فارغ (لم يُرسل data أو content)")
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
        
        # حفظ الملف مع معالجة شاملة للأخطاء
        try:
            # التأكد من وجود المجلد
            upload_dir = os.path.dirname(file_path)
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                print(f"تم إنشاء مجلد الرفع: {upload_dir}")
            
            # التحقق من صحة المسار بشكل شامل
            is_valid_path = False
            try:
                # التأكد من أن المسار مطلق وخالي من أحرف التحكم
                is_valid_path = (os.path.isabs(file_path) and 
                                '\0' not in file_path and 
                                '\b' not in file_path and
                                '\f' not in file_path and
                                '\v' not in file_path and
                                '\a' not in file_path and
                                len(file_path) < 240 and
                                os.path.normpath(file_path) == file_path)
            except Exception as path_error:
                print(f"خطأ في التحقق من صحة المسار: {str(path_error)}")
                is_valid_path = False
            
            if is_valid_path:
                save_attempts = 0
                max_attempts = 3
                saved_successfully = False
                
                while save_attempts < max_attempts and not saved_successfully:
                    try:
                        save_attempts += 1
                        with open(file_path, 'wb') as f:
                            f.write(file_bytes)
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            saved_successfully = True
                            print(f"تم حفظ الملف في المحاولة {save_attempts}: {file_path}")
                        else:
                            print(f"المحاولة {save_attempts}: الملف لم يتم حفظه بشكل صحيح")
                    except Exception as write_error:
                        print(f"خطأ في كتابة الملف (محاولة {save_attempts}): {str(write_error)}")
                        if save_attempts == max_attempts:
                            raise write_error
                
                if not saved_successfully:
                    raise Exception("فشلت جميع محاولات حفظ الملف")
            else:
                print(f"مسار الملف غير صالح: {file_path}")
                # استخدام آلية متعددة المراحل للمسارات البديلة
                save_attempts = 0
                max_attempts = 3
                saved_successfully = False
                last_error = None
                
                while save_attempts < max_attempts and not saved_successfully:
                    try:
                        save_attempts += 1
                        timestamp = int(time.time())
                        
                        # اختيار مسار مختلف في كل محاولة
                        if save_attempts == 1:
                            # المحاولة الأولى: في مجلد الرفع
                            safe_filename = f"safe_file_{timestamp}_{save_attempts}.bin"
                            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
                        elif save_attempts == 2:
                            # المحاولة الثانية: في المجلد الأب لمجلد الرفع
                            safe_filename = f"alt_file_{timestamp}_{save_attempts}.bin"
                            file_path = os.path.join(os.path.dirname(UPLOAD_FOLDER), safe_filename)
                        else:
                            # المحاولة الثالثة: في مسار مطلق بسيط
                            file_path = os.path.abspath(f"emergency_{timestamp}.bin")
                        
                        print(f"محاولة {save_attempts}: استخدام المسار البديل: {file_path}")
                        
                        # التأكد من وجود المجلد
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        # محاولة الحفظ
                        with open(file_path, 'wb') as f:
                            f.write(file_bytes)
                        
                        # التحقق من نجاح الحفظ
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            saved_successfully = True
                            print(f"تم حفظ الملف بنجاح في المسار البديل (محاولة {save_attempts}): {file_path}")
                        else:
                            print(f"المحاولة {save_attempts}: الملف لم يتم حفظه بشكل صحيح في المسار البديل")
                    except Exception as save_error:
                        last_error = save_error
                        print(f"فشل المحاولة {save_attempts} في المسار البديل: {str(save_error)}")
                
                # التحقق النهائي من نجاح الحفظ
                if not saved_successfully:
                    print(f"فشلت جميع محاولات حفظ الملف في المسارات البديلة: {str(last_error)}")
                    # محاولة أخيرة باستخدام مسار مؤقت
                    try:
                        import tempfile
                        temp_dir = tempfile.gettempdir()
                        temp_file = os.path.join(temp_dir, f"qarun_hotel_doc_{int(time.time())}.bin")
                        with open(temp_file, 'wb') as f:
                            f.write(file_bytes)
                        file_path = temp_file
                        print(f"تم حفظ الملف في المجلد المؤقت للنظام: {file_path}")
                    except Exception as temp_error:
                        print(f"فشل في الحفظ في المجلد المؤقت: {str(temp_error)}")
                        return None
        except Exception as e:
            print(f"خطأ في حفظ الملف على القرص: {str(e)}")
            current_app.logger.error(f'Error writing file to disk: {str(e)}', exc_info=True)
            
            # محاولة حفظ الملف باسم آمن تماماً
            try:
                timestamp = int(time.time())
                safe_filename = f"safe_file_{timestamp}.bin"
                # استخدام المسار المطلق للمجلد
                safe_path = os.path.join(UPLOAD_FOLDER, safe_filename)
                
                # التأكد من وجود المجلد
                os.makedirs(os.path.dirname(safe_path), exist_ok=True)
                
                with open(safe_path, 'wb') as f:
                    f.write(file_bytes)
                file_path = safe_path
                print(f"تم حفظ الملف في المحاولة الثانية: {file_path}")
            except Exception as retry_error:
                print(f"فشل في المحاولة الثانية لحفظ الملف: {str(retry_error)}")
                
                # محاولة ثالثة باستخدام مسار مختلف تماماً
                try:
                    timestamp = int(time.time())
                    alt_filename = f"emergency_{timestamp}.bin"
                    alt_path = os.path.abspath(os.path.join('hotel', 'static', 'uploads', alt_filename))
                    
                    # التأكد من وجود المجلد
                    os.makedirs(os.path.dirname(alt_path), exist_ok=True)
                    
                    with open(alt_path, 'wb') as f:
                        f.write(file_bytes)
                    file_path = alt_path
                    print(f"تم حفظ الملف في المحاولة الثالثة: {file_path}")
                except Exception as final_error:
                    print(f"فشل في جميع محاولات حفظ الملف: {str(final_error)}")
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
            timestamp = int(time.time())
            emergency_filename = f"emergency_file_{timestamp}.jpg"
            
            # التأكد من وجود مجلد الرفع
            create_upload_folder()
            
            data_url = doc_data.get('data', '') if doc_data else ''
            if data_url and ',' in data_url:
                header, encoded = data_url.split(',', 1)
                # محاولة فك تشفير البيانات مع معالجة الأخطاء
                file_bytes = None
                try:
                    file_bytes = base64.b64decode(encoded)
                except Exception as decode_error:
                    print(f"خطأ في فك تشفير البيانات الطارئة: {str(decode_error)}")
                    # محاولة إصلاح البيانات المشفرة
                    encoded = encoded.replace(' ', '+')
                    try:
                        file_bytes = base64.b64decode(encoded)
                        print("تم إصلاح البيانات المشفرة في المحاولة الطارئة")
                    except Exception as retry_decode_error:
                        print(f"فشل في فك تشفير البيانات في المحاولة الطارئة: {str(retry_decode_error)}")
                        # محاولة أخيرة لفك التشفير بعد تنظيف البيانات
                        try:
                            # إزالة الأحرف غير الصالحة
                            clean_encoded = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
                            # إضافة علامات = للتبطين إذا لزم الأمر
                            padding = len(clean_encoded) % 4
                            if padding:
                                clean_encoded += '=' * (4 - padding)
                            file_bytes = base64.b64decode(clean_encoded)
                            print("تم فك التشفير بعد تنظيف البيانات")
                        except Exception:
                            print("فشل في جميع محاولات فك التشفير")
                            return None
                
                if file_bytes and len(file_bytes) > 0:
                    # استخدام اسم ملف آمن تماماً
                    timestamp = int(time.time())
                    unique_filename = f"emrg_{timestamp}_{len(file_bytes)}.jpg"
                    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                    
                    # التأكد من وجود المجلد
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # محاولة حفظ الملف مع معالجة الأخطاء
                    try:
                        with open(file_path, 'wb') as f:
                            f.write(file_bytes)
                        print(f"تم حفظ الملف الطارئ في: {file_path}")
                    except Exception as save_error:
                        print(f"خطأ في حفظ الملف الطارئ: {str(save_error)}")
                        # محاولة بمسار مختلف
                        try:
                            alt_path = os.path.join(os.path.dirname(UPLOAD_FOLDER), f"emrg_{timestamp}.jpg")
                            os.makedirs(os.path.dirname(alt_path), exist_ok=True)
                            with open(alt_path, 'wb') as f:
                                f.write(file_bytes)
                            unique_filename = os.path.basename(alt_path)
                            file_path = alt_path
                            print(f"تم حفظ الملف الطارئ في المسار البديل: {file_path}")
                        except Exception as alt_save_error:
                            print(f"فشل في المسار البديل: {str(alt_save_error)}")
                            # محاولة أخيرة في مجلد الجذر
                            try:
                                root_path = os.path.abspath(f"emergency_{timestamp}.jpg")
                                with open(root_path, 'wb') as f:
                                    f.write(file_bytes)
                                unique_filename = os.path.basename(root_path)
                                file_path = root_path
                                print(f"تم حفظ الملف الطارئ في المحاولة الأخيرة: {file_path}")
                            except Exception as final_error:
                                print(f"فشل في جميع محاولات الحفظ الطارئة: {str(final_error)}")
                                return None
                    
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